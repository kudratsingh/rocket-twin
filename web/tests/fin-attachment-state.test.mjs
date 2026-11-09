import assert from 'node:assert/strict';
import test from 'node:test';
import { createServer } from '../node_modules/vite/dist/node/index.js';

async function withState(run) {
  const server = await createServer({
    configFile: false,
    root: new URL('..', import.meta.url).pathname,
    server: { middlewareMode: true, hmr: false, ws: false },
    appType: 'custom',
  });
  try {
    await run(await server.ssrLoadModule('/src/fin-attachment/finAttachmentState.ts'));
  } finally {
    await server.close();
  }
}

test('actual Design scene retention is confined to the exact source joint Engineering journey', async () => {
  await withState(route => {
    const href = route.openFinDrawingHref('/', route.initialFinAttachmentState, 'fin_tabs', 'root');
    const source = {id:'G80-F2-RP1-AD1-definition-v2',identity:{specification_sha256:'811b3bed631fe2ce30a6b0211beecb739d40ebbbcb10e063f6beba0854631660',inspection_geometry_sha256:route.FIN_ATTACHMENT_GEOMETRY_REVISION}};
    assert.equal(route.retainFinDesignWorkspace('design', null, '/'), true);
    assert.equal(route.retainFinDesignWorkspace('engineering', source, href), true);
    assert.equal(route.retainFinDesignWorkspace('engineering', source, '/?workspace=engineering'), false);
    for(const mode of ['experiments','replay','analysis']) assert.equal(route.retainFinDesignWorkspace(mode, source, href), false);
    for(const identity of [{...source.identity,specification_sha256:'0'.repeat(64)},{...source.identity,inspection_geometry_sha256:'0'.repeat(64)}]) assert.equal(route.retainFinDesignWorkspace('engineering',{...source,identity},href), false);
    assert.equal(route.retainFinDesignWorkspace('engineering',{...source,id:'archived'},href), false);
  });
});

test('exact RP1 fin attachment state round-trips between Design and Engineering', async () => {
  await withState((route) => {
    const state = {
      ...route.initialFinAttachmentState,
      section: 'longitudinal',
      selectedPieceId: 'fin_tabs',
      selectedDimensionId: 'slot-width',
      isolatedPieceIds: ['fin_tabs', 'body'],
      hiddenPieceIds: ['aft_ring'],
      partsSidebarOpen: false,
      evidenceSidebarOpen: true,
    };
    const design = route.finAttachmentHref('/?workspace=design', state, 'fin_set');
    const parsed = route.parseFinAttachmentHref(design);
    assert.ok(parsed);
    assert.equal(parsed.originPartId, 'fin_set');
    assert.equal(parsed.drawing, null);
    assert.deepEqual(parsed.state, state);
    assert.match(design, /jointGeometry=238d01e5/);
    assert.match(design, /jointDetail=1b810376/);
    assert.match(design, /jointSection=longitudinal/);
    assert.match(design, /jointDimension=slot-width/);
    const engineering = route.openFinDrawingHref(design, state, 'fin_set', 'loadpath');
    assert.equal(new URL(engineering, 'http://local.invalid').searchParams.get('part'), 'fin_tabs');
    assert.match(engineering, /workspace=engineering/);
    assert.match(engineering, /view=rp1-connections/);
    assert.match(engineering, /connection=fin-root/);
    assert.equal(route.parseFinAttachmentHref(engineering).drawing, 'loadpath');
    const changedEngineeringPart = engineering.replace('part=fin_tabs', 'part=motor_tube');
    const returned = route.returnFinJointHref(changedEngineeringPart);
    assert.ok(returned);
    assert.equal(new URL(returned, 'http://local.invalid').searchParams.get('part'), 'fin_set');
    assert.deepEqual(route.parseFinAttachmentHref(returned).state, state);
    assert.doesNotMatch(returned, /jointDrawing|connection=|view=/);
  });
});

test('invalid or ambiguous source, piece, section, dimension, and visibility state is refused', async () => {
  await withState((route) => {
    const href = route.finAttachmentHref('/', route.initialFinAttachmentState, 'fin_set');
    const bad = [
      href.replace('finJoint=1', 'finJoint=1&finJoint=1'),
      href.replace('jointSection=assembled', 'jointSection=oblique'),
      href.replace('part=fin_set', 'part=bogus'),
      href.replace('jointOrigin=fin_set', 'jointOrigin=bogus'),
      href.replace('jointGeometry=238d01e5', 'jointGeometry=deadbeef'),
      href.replace('jointDetail=1b810376', 'jointDetail=deadbeef'),
      href.replace('jointSection=assembled', 'jointSection=assembled&jointPiece=bogus'),
      `${href}&jointDimension=invented`,
      `${href}&jointIsolate=fin_set,fin_set`,
      `${href}&jointHidden=not_a_piece`,
      `${href}&jointUnknown=1`,
      href.replace('jointParts=1', 'jointParts=yes'),
      href.replace('spec=811b', 'spec=dead'),
    ];
    bad.forEach((candidate) => assert.equal(route.parseFinAttachmentHref(candidate), null));
    assert.equal(route.returnFinJointHref('/?workspace=design'), null);
    assert.throws(() =>
      route.finAttachmentHref('/?design=foreign', route.initialFinAttachmentState, 'fin_set'),
    );
    assert.throws(() =>
      route.finAttachmentHref('/', route.initialFinAttachmentState, 'not_a_piece'),
    );
    assert.throws(() =>
      route.openFinDrawingHref('/', route.initialFinAttachmentState, 'fin_set', 'unrecorded'),
    );
    assert.equal(
      route.validFinAttachmentState({
        ...route.initialFinAttachmentState,
        isolatedPieceIds: ['fin_tabs'],
        hiddenPieceIds: ['fin_tabs'],
      }),
      false,
    );
  });
});

test('camera snapshot is finite identity-keyed local state, not an inferred URL camera', async () => {
  await withState((route) => {
    const camera = {
      position: [0.2, -0.1, 0.5],
      target: [0, 0, 0.12],
      up: [0, 0, 1],
      zoom: 1.5,
    };
    const parsed = route.parseFinAttachmentCameraSnapshot(camera);
    assert.deepEqual(parsed, camera);
    assert.notEqual(parsed.position, camera.position);
    const href = route.finAttachmentHref(
      '/',
      { ...route.initialFinAttachmentState, camera },
      'motor_tube',
    );
    assert.equal(route.parseFinAttachmentHref(href).state.camera, null);
    assert.doesNotMatch(href, /camera|position|target|zoom/);
    assert.match(route.finAttachmentSessionKey('motor_tube'), /238d01e5.*motor_tube$/);
    assert.equal(route.parseFinAttachmentCameraSnapshot({ ...camera, zoom: Infinity }), null);
    assert.equal(
      route.parseFinAttachmentCameraSnapshot({ ...camera, position: [0, 0, 0.12] }),
      null,
    );
    assert.equal(route.parseFinAttachmentCameraSnapshot({ ...camera, up: [0, 0, 0] }), null);
    assert.equal(route.parseFinAttachmentCameraSnapshot({ ...camera, target: [NaN, 0, 0] }), null);
  });
});
