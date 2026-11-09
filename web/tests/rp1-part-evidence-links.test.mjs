import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import {
  RP1_CONNECTION_PART_IDS,
  RP1_CONNECTIONS_CONFIGURATION,
  RP1_CONNECTIONS_SHA256,
  rp1ConnectionDesignHref,
} from '../src/workbench/rp1Connections.ts';
import {
  RP1_INSPECTION_GEOMETRY_SHA256,
  rp1PartEvidenceLinks,
} from '../src/workbench/rp1PartEvidenceLinks.ts';

const recordedBytes = readFileSync(
  new URL(
    '../../docs/studies/frontend-desktop-detail-20261108/rp1-connections-fixture.json',
    import.meta.url,
  ),
);
assert.equal(
  createHash('sha256').update(recordedBytes).digest('hex'),
  '7087e7dc7434a0c4d309055d7897ee79bb140e58e30b24499579e65d5e6b328e',
  'tracked fixture must remain byte-identical to the verified RP1 connection export',
);
const recorded = JSON.parse(recordedBytes);
const source = () => ({
  id: RP1_CONNECTIONS_CONFIGURATION,
  identity: {
    configuration_id: RP1_CONNECTIONS_CONFIGURATION,
    specification_sha256: RP1_CONNECTIONS_SHA256,
    inspection_geometry_sha256: RP1_INSPECTION_GEOMETRY_SHA256,
  },
  parts: RP1_CONNECTION_PART_IDS.map((id) => ({ id })),
  summary: {},
});
const params = (href) => new URL(href, 'http://local.test').searchParams;

test('forward ring has two explicit source-pinned destinations from the tracked record', () => {
  const result = rp1PartEvidenceLinks(source(), 'forward_ring', recorded);
  assert.equal(result.status, 'available');
  assert.deepEqual(
    result.links.map((link) => link.id),
    ['fin-root', 'recovery'],
  );
  for (const link of result.links) {
    const url = params(link.href);
    assert.equal(url.get('workspace'), 'engineering');
    assert.equal(url.get('view'), 'rp1-connections');
    assert.equal(url.get('design'), RP1_CONNECTIONS_CONFIGURATION);
    assert.equal(url.get('spec'), RP1_CONNECTIONS_SHA256);
    assert.equal(url.get('part'), 'forward_ring');
    assert.equal(url.get('connection'), link.id);
  }
  assert.match(result.sourceStatus, /unadopted concepts/);
});

test('fin-only part gets one route; unrelated source part gets explicit unavailable mapping', () => {
  const fin = rp1PartEvidenceLinks(source(), 'fin_tabs', recorded);
  assert.equal(fin.status, 'available');
  assert.deepEqual(
    fin.links.map((link) => link.id),
    ['fin-root'],
  );
  const noGraph = rp1PartEvidenceLinks(source(), 'baro', recorded);
  assert.equal(noGraph.status, 'unmapped');
  assert.deepEqual(noGraph.links, []);
  assert.match(noGraph.message, /No relationship is inferred/);
});

test('foreign, stale, incomplete or unselected source cannot acquire an evidence route', () => {
  const base = source();
  for (const changed of [
    { ...base, id: 'modular-performance-v1' },
    { ...base, identity: { ...base.identity, configuration_id: 'modular-performance-v1' } },
    { ...base, identity: { ...base.identity, specification_sha256: 'b'.repeat(64) } },
    { ...base, identity: { ...base.identity, inspection_geometry_sha256: 'b'.repeat(64) } },
    { ...base, parts: base.parts.slice(1) },
    { ...base, parts: [...base.parts.slice(1), base.parts[1]] },
  ]) {
    const result = rp1PartEvidenceLinks(changed, 'forward_ring', recorded);
    assert.equal(result.status, 'unavailable');
    assert.deepEqual(result.links, []);
  }
  assert.equal(rp1PartEvidenceLinks(base, 'foreign', recorded).status, 'unavailable');
  const foreignDocument = structuredClone(recorded);
  foreignDocument.configuration.sha256 = 'b'.repeat(64);
  assert.equal(rp1PartEvidenceLinks(base, 'forward_ring', foreignDocument).status, 'unavailable');
  const staleFingerprint = structuredClone(recorded);
  staleFingerprint.sources[1].sha256 = 'b'.repeat(64);
  assert.equal(rp1PartEvidenceLinks(base, 'forward_ring', staleFingerprint).status, 'unavailable');
  const alteredMembership = structuredClone(recorded);
  alteredMembership.connections[1].part_ids.push('baro');
  alteredMembership.connections[1].nodes[0].part_ids.push('baro');
  assert.equal(rp1PartEvidenceLinks(base, 'baro', alteredMembership).status, 'unavailable');
});

test('return to Design retains only a verified connection containing the selected part', () => {
  const recovery = params(
    rp1ConnectionDesignHref('forward_ring', { connectionId: 'recovery', document: recorded }),
  );
  assert.equal(recovery.get('workspace'), 'design');
  assert.equal(recovery.get('design'), RP1_CONNECTIONS_CONFIGURATION);
  assert.equal(recovery.get('spec'), RP1_CONNECTIONS_SHA256);
  assert.equal(recovery.get('part'), 'forward_ring');
  assert.equal(recovery.get('connection'), 'recovery');
  assert.equal(params(rp1ConnectionDesignHref('forward_ring')).has('connection'), false);
  assert.throws(
    () => rp1ConnectionDesignHref('fin_tabs', { connectionId: 'recovery', document: recorded }),
    /does not contain/,
  );
  assert.throws(
    () => rp1ConnectionDesignHref('forward_ring', { connectionId: 'foreign', document: recorded }),
    /does not contain/,
  );
  const stale = structuredClone(recorded);
  stale.configuration.sha256 = 'b'.repeat(64);
  assert.throws(
    () => rp1ConnectionDesignHref('forward_ring', { connectionId: 'recovery', document: stale }),
    /configuration identity/,
  );
  const alteredMembership = structuredClone(recorded);
  alteredMembership.connections[1].part_ids.push('fin_tabs');
  alteredMembership.connections[1].nodes[0].part_ids.push('fin_tabs');
  assert.throws(
    () =>
      rp1ConnectionDesignHref('fin_tabs', {
        connectionId: 'recovery',
        document: alteredMembership,
      }),
    /route membership changed/,
  );
});
