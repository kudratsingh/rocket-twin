import assert from 'node:assert/strict';
import test from 'node:test';
import { readPartLink, partHref } from '../src/workspaces/partLinks.ts';
import { designHref } from '../src/workspaces/navigation.ts';

const AD1 = 'G80-F2-RP1-AD1-definition-v2';
const SPEC = '811b3bed631fe2ce30a6b0211beecb739d40ebbbcb10e063f6beba0854631660';
// Compact synthetic source-shaped fixture: actual IDs/revision, no physical values.
const source = () => ({
  id: AD1,
  summary: {},
  identity: { specification_sha256: SPEC, cad_revision_sha256: null },
  parts: [
    { id: 'fin_tabs', type: 'allowance', parent: null, material: '', learn: '' },
    { id: 'body', type: 'tube', parent: null, material: '', learn: '' },
  ],
});
const url = (href) => new URL(href, 'http://local.test');
const search = (entries) => `?${new URLSearchParams(entries)}`;
const validEntries = { workspace: 'design', design: AD1, spec: SPEC, part: 'fin_tabs' };

test('exact AD1 part and full revision round-trip through Design and Engineering', () => {
  const document = source();
  const engineering = url(
    partHref('/?workspace=design&unrelated=keep#evidence', document, 'fin_tabs', 'engineering'),
  );
  assert.equal(engineering.searchParams.get('workspace'), 'engineering');
  assert.equal(engineering.searchParams.get('view'), 'rp1-connections');
  assert.equal(engineering.searchParams.get('design'), AD1);
  assert.equal(engineering.searchParams.get('spec'), SPEC);
  assert.equal(engineering.searchParams.get('part'), 'fin_tabs');
  assert.equal(engineering.searchParams.get('unrelated'), 'keep');
  assert.equal(engineering.hash, '#evidence');
  assert.deepEqual(readPartLink(engineering.search, document), { part: 'fin_tabs', notice: null });
  const design = url(partHref(engineering.href, document, 'body', 'design'));
  assert.equal(design.searchParams.get('workspace'), 'design');
  const analysis = url(partHref(design.href, document, 'body', 'analysis'));
  assert.equal(analysis.searchParams.get('workspace'), 'analysis');
  assert.deepEqual(readPartLink(analysis.search, document), { part: 'body', notice: null });
  assert.equal(design.searchParams.get('spec'), SPEC);
  assert.deepEqual(readPartLink(design.search, document), { part: 'body', notice: null });
  const clear = url(partHref(design.href, document, null));
  assert.equal(clear.searchParams.has('part'), false);
  assert.equal(clear.searchParams.get('design'), AD1);
  assert.equal(clear.searchParams.get('spec'), SPEC);
  assert.deepEqual(readPartLink(clear.search, document), { part: null, notice: null });
  assert.throws(() => partHref('/', document, 'archived-body'), /Unknown source part/);
});

test('wrong source, revision, part or absent required context cannot select a part', () => {
  const document = source();
  for (const patch of [
    { design: 'modular-performance-v1' },
    { spec: 'b'.repeat(64) },
    { part: 'foreign' },
    { part: '' },
    { spec: '' },
  ]) {
    const result = readPartLink(search({ ...validEntries, ...patch }), document);
    assert.equal(result.part, null);
    assert.match(result.notice, /unavailable/);
  }
  for (const missing of ['design', 'spec']) {
    const entries = { ...validEntries };
    delete entries[missing];
    const result = readPartLink(search(entries), document);
    assert.equal(result.part, null);
    assert.match(result.notice, /No historical part is substituted/);
  }
  assert.deepEqual(
    readPartLink('', document),
    { part: null, notice: null },
    'an unselected overview needs no part context',
  );
});

test('duplicate identity parameters are rejected even when duplicate values happen to agree', () => {
  for (const key of ['design', 'spec', 'part', 'cad']) {
    for (const duplicate of [key === 'cad' ? 'stale-cad' : validEntries[key], 'different-value']) {
      const params = new URLSearchParams(validEntries);
      if (key === 'cad') params.append(key, 'stale-cad');
      params.append(key, duplicate);
      const result = readPartLink(`?${params}`, source());
      assert.equal(result.part, null, key);
      assert.match(result.notice, /unavailable/, key);
    }
  }
});

test('CAD pin is compared only with the exact source, including unavailable AD1 CAD', () => {
  assert.match(
    readPartLink(search({ ...validEntries, cad: 'old-cad' }), source()).notice,
    /unavailable/,
  );
  const archived = {
    ...source(),
    id: 'archived-fixture',
    identity: { resolved_spec_sha256: 'c'.repeat(64), cad_revision_sha256: 'd'.repeat(64) },
  };
  const good = search({
    design: archived.id,
    spec: 'c'.repeat(64),
    cad: 'd'.repeat(64),
    part: 'body',
  });
  assert.deepEqual(readPartLink(good, archived), { part: 'body', notice: null });
  assert.match(
    readPartLink(good.replace('d'.repeat(64), 'e'.repeat(64)), archived).notice,
    /unavailable/,
  );
});

test('generated source links remove stale or duplicate CAD pins instead of producing self-invalidating links', () => {
  for (const incoming of ['/inspect?cad=old-cad', '/inspect?cad=old-cad&cad=another-old-cad']) {
    const generated = url(partHref(incoming, source(), 'fin_tabs', 'engineering'));
    assert.equal(
      generated.searchParams.has('cad'),
      false,
      'AD1 has no CAD fingerprint to preserve',
    );
    assert.deepEqual(readPartLink(generated.search, source()), { part: 'fin_tabs', notice: null });
  }
});

test('missing source fingerprint cannot be converted into an exact-revision part link', () => {
  const unidentified = {
    ...source(),
    identity: { specification_sha256: null, resolved_spec_sha256: null },
  };
  assert.throws(
    () => partHref('/', unidentified, 'fin_tabs'),
    /revision|fingerprint|source|identity/i,
  );
  const emptyPin = readPartLink(search({ ...validEntries, spec: '' }), unidentified);
  assert.equal(emptyPin.part, null);
  assert.match(emptyPin.notice, /unavailable/);
});

test('configuration switch clears source-specific part, revision, connection and result context', () => {
  const initial = search({
    ...validEntries,
    cad: 'stale',
    connection: 'fin-root',
    run: 'recorded-run',
    result: 'result-id',
    compare: 'comparison-id',
    view: 'rp1-connections',
    unrelated: 'keep',
  });
  const switched = url(designHref(`/inspect${initial}#anchor`, 'different-design'));
  assert.equal(switched.searchParams.get('design'), 'different-design');
  for (const key of ['spec', 'part', 'cad', 'connection', 'run', 'result', 'compare'])
    assert.equal(switched.searchParams.has(key), false, key);
  assert.equal(switched.searchParams.get('unrelated'), 'keep');
  assert.equal(switched.hash, '#anchor');
  assert.equal(switched.pathname, '/inspect');
  const same = url(designHref(`/inspect${search(validEntries)}`, AD1));
  assert.equal(same.searchParams.get('part'), 'fin_tabs');
  assert.equal(same.searchParams.get('spec'), SPEC);
});
