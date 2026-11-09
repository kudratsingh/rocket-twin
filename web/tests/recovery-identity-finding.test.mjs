import assert from 'node:assert/strict';
import test from 'node:test';
import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import React from '../node_modules/react/index.js';
import { renderToStaticMarkup } from '../node_modules/react-dom/server.node.js';
import { createServer } from '../node_modules/vite/dist/node/index.js';
import {
  recoveryIdentityFinding,
  RECOVERY_IDENTITY_REPORT_SHA256,
} from '../src/components/recoveryIdentityFinding.ts';

const core = JSON.parse(
  readFileSync(
    new URL('../../docs/studies/rp1-inspection-geometry-20261107/manifest.json', import.meta.url),
  ),
);
const reportBytes = readFileSync(
  new URL(
    '../../docs/studies/frontend-desktop-detail-20261108/next-detail-sources.json',
    import.meta.url,
  ),
);
const report = JSON.parse(reportBytes);
function document() {
  return {
    id: core.id,
    identity: { ...core.identity },
    summary: {},
    parts: core.parts.map((row) => ({
      id: row.id,
      material: 'source',
      learn: '',
      inspection_shape_sha256: row.inspection_shape_sha256,
      representation: { role: row.maturity },
      mesh_url: row.mesh ? `/registered/${row.id}.glb` : null,
    })),
  };
}
const selected = (vehicle) => vehicle.parts.find((part) => part.id === 'independent_recovery');

test('current exact source registers both controller names and source locators without choosing hardware', () => {
  assert.equal(
    createHash('sha256').update(reportBytes).digest('hex'),
    RECOVERY_IDENTITY_REPORT_SHA256,
  );
  assert.equal(report.frozen_source.sha256, core.identity.specification_sha256);
  assert.equal(
    createHash('sha256')
      .update(readFileSync(new URL(`../../${report.frozen_source.path}`, import.meta.url)))
      .digest('hex'),
    report.frozen_source.sha256,
  );
  const record = report.components.find((item) => item.part_id === 'independent_recovery');
  assert.equal(record.exact_installed_identity, 'unresolved');
  const vehicle = document(),
    before = JSON.stringify(vehicle);
  const finding = recoveryIdentityFinding(vehicle, selected(vehicle));
  assert.equal(finding.state, 'unresolved');
  assert.equal(finding.proposedName, 'Eggtimer Apogee');
  assert.equal(finding.legacyName, 'Altus Metrum EasyMini v3.0');
  assert.deepEqual(finding.primaryLocators, record.source_conflict.primary_locators);
  assert.equal(finding.legacyLocator, 'parts[id=independent_recovery].engineering.function');
  assert.equal(finding.sourcePath, report.frozen_source.path);
  assert.equal(finding.inspectionGeometrySha256, core.identity.inspection_geometry_sha256);
  assert.equal(JSON.stringify(vehicle), before);
});
test('foreign/current-object mismatch, changed part shape/maturity and unrelated meshless records suppress finding', () => {
  for (const mutate of [
    (v) => {
      v.id = 'historical';
    },
    (v) => {
      v.identity.configuration_id = 'foreign';
    },
    (v) => {
      v.identity.specification_sha256 = '0'.repeat(64);
    },
    (v) => {
      v.identity.inspection_geometry_sha256 = '0'.repeat(64);
    },
    (v) => {
      selected(v).inspection_shape_sha256 = '0'.repeat(64);
    },
    (v) => {
      selected(v).representation.role = 'manufactured';
    },
    (v) => {
      v.parts.pop();
    },
  ]) {
    const vehicle = document();
    mutate(vehicle);
    assert.equal(recoveryIdentityFinding(vehicle, selected(vehicle)), null);
  }
  const vehicle = document(),
    part = selected(vehicle);
  assert.equal(recoveryIdentityFinding(vehicle, { ...part }), null);
  assert.equal(recoveryIdentityFinding(vehicle), null);
  assert.equal(
    recoveryIdentityFinding(
      vehicle,
      vehicle.parts.find((item) => !item.mesh_url),
    ),
    null,
  );
  assert.equal(recoveryIdentityFinding(vehicle, vehicle.parts[0]), null);
});
test('missing mesh or arbitrary box dimensions do not resolve or invent the source finding', () => {
  const vehicle = document(),
    part = selected(vehicle);
  part.mesh_url = null;
  part.geometry = {};
  assert.equal(recoveryIdentityFinding(vehicle, part).state, 'unresolved');
  part.geometry = { bbox_m: [100, 200, 300] };
  assert.equal(recoveryIdentityFinding(vehicle, part).state, 'unresolved');
});
test('SSR notice explains both names and generic envelope limits, with no export/action controls', async () => {
  const server = await createServer({
    configFile: false,
    root: new URL('..', import.meta.url).pathname,
    server: { middlewareMode: true, hmr: false, ws: false },
    appType: 'custom',
  });
  try {
    const { RecoveryIdentityNotice } = await server.ssrLoadModule(
      '/src/components/RecoveryIdentityNotice.tsx',
    );
    const vehicle = document(),
      part = selected(vehicle);
    const render = (props) =>
      renderToStaticMarkup(React.createElement(RecoveryIdentityNotice, props));
    const html = render({ vehicle, selectedPart: part });
    assert.match(html, /Eggtimer Apogee/);
    assert.match(html, /Altus Metrum EasyMini v3.0/);
    assert.match(html, /generic estimated envelope/);
    assert.match(html, /not controller-specific CAD/);
    assert.match(html, /power details remain unresolved/);
    assert.match(html, /engineering.function/);
    assert.ok(html.includes(report.frozen_source.sha256));
    assert.match(html, /next-detail-sources.md/);
    assert.doesNotMatch(html, /<button|disabled=|mailto:|electrical pass|electrical fail/);
    assert.equal(render({ vehicle, selectedPart: { ...part } }), '');
    assert.equal(render({ vehicle, selectedPart: null }), '');
  } finally {
    await server.close();
  }
});
