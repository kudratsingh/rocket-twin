import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import React from '../node_modules/react/index.js';
import { renderToStaticMarkup } from '../node_modules/react-dom/server.node.js';
import { createServer } from '../node_modules/vite/dist/node/index.js';

const auditBytes = readFileSync(
  new URL(
    '../../docs/studies/frontend-flight-computer-source-20261109/source-manifest.json',
    import.meta.url,
  ),
);
const audit = JSON.parse(auditBytes);
const bank = JSON.parse(readFileSync(new URL('./fixtures/rp1-parts-bank.json', import.meta.url)));
function vehicle() {
  return {
    id: bank.configuration_id,
    identity: { ...bank.identity },
    parts: bank.definitions.map((definition) => ({
      id: definition.source_part_id,
      type: definition.kind,
      parent: null,
      material: definition.material,
      learn: '',
      estimate: definition.source_estimate,
      geometry: definition.dimensions.values,
      mass_kg: definition.mass_kg,
    })),
    summary: {},
  };
}
function selected(document) {
  return document.parts.find((part) => part.id === 'flight_computer');
}

test('flight-computer source finding uses the actual manifest and stays scoped to the frozen source', async (t) => {
  const vite = await createServer({
    configFile: false,
    root: new URL('..', import.meta.url).pathname,
    server: { middlewareMode: true, hmr: false, ws: false },
    appType: 'custom',
    logLevel: 'silent',
  });
  try {
    const source = await vite.ssrLoadModule('/src/components/FlightComputerSourceFinding.tsx');
    const render = (document, part) =>
      renderToStaticMarkup(
        React.createElement(source.FlightComputerSourceFinding, {
          vehicle: document,
          selectedPart: part,
        }),
      );

    await t.test(
      'actual local manifest/source bytes pin an unidentified estimate and unadopted reference',
      () => {
        assert.equal(
          createHash('sha256').update(auditBytes).digest('hex'),
          source.FLIGHT_COMPUTER_SOURCE_MANIFEST_SHA256,
        );
        const specification = audit.local_inputs.find(
          (input) => input.path === bank.identity.specification_path,
        );
        assert.equal(specification.sha256, bank.identity.specification_sha256);
        assert.equal(
          createHash('sha256')
            .update(readFileSync(new URL(`../../${specification.path}`, import.meta.url)))
            .digest('hex'),
          specification.sha256,
        );
        assert.equal(audit.frozen_source.exact_product, null);
        assert.equal(audit.frozen_source.exact_manufacturer, null);
        assert.equal(audit.frozen_source.exact_revision, null);
        const document = vehicle(),
          part = selected(document);
        assert.deepEqual(
          part.geometry.bbox_m.map((value) => value * 1000),
          audit.frozen_source.bbox_mm,
        );
        assert.equal(part.mass_kg, audit.frozen_source.mass_kg);
        assert.equal(part.estimate, true);
        assert.equal(audit.reference_lead.adopted, false);
        assert.equal(audit.reference_lead.populated_height_mm, null);
        assert.equal(audit.licence_and_redistribution.derived_populated_asset_admitted, false);
        const before = JSON.stringify(document);
        assert.equal(source.hasFlightComputerSourceFinding(document, part), true);
        assert.equal(JSON.stringify(document), before);
      },
    );

    await t.test('wrong design/specification/configuration/selected part has no finding', () => {
      for (const mutate of [
        (document) => {
          document.id = 'modular-performance-v1';
        },
        (document) => {
          document.identity.specification_sha256 = '0'.repeat(64);
        },
        (document) => {
          document.identity.configuration_id = 'other';
        },
        (document) => {
          document.identity = undefined;
        },
      ]) {
        const document = vehicle();
        mutate(document);
        assert.equal(render(document, selected(document)), '');
      }
      const document = vehicle(),
        part = selected(document);
      assert.equal(render(document, null), '');
      assert.equal(render(document, { ...part }), '');
      assert.equal(
        render(
          document,
          document.parts.find((row) => row.id === 'high_g_accel'),
        ),
        '',
      );
      assert.equal(
        render(
          document,
          document.parts.find((row) => row.id === 'independent_recovery'),
        ),
        '',
      );
    });

    await t.test(
      'readable SSR distinguishes unavailable current hardware from the unselected official reference',
      () => {
        const document = vehicle();
        const html = render(document, selected(document));
        assert.match(html, /Flight-computer product not selected/);
        assert.match(html, /generic Cortex-M7/);
        assert.match(html, /61 × 18 × 6 mm and 12 g are estimates/);
        assert.match(html, /detailed board CAD is unavailable/);
        assert.match(html, /Actual populated height, mounting/);
        assert.match(html, /Teensy 4.1 is not selected/);
        assert.match(html, /unadopted reference/);
        assert.match(html, /0.04 mm shorter and 0.22 mm narrower/);
        assert.match(html, /Similar dimensions do not identify the board or prove fit/);
        assert.match(html, /No part replacement or mass credit/);
        assert.match(html, /aria-label="Flight computer source identity"/);
        assert.match(html, /<details><summary>/);
        assert.ok(html.includes('https://www.pjrc.com/store/teensy41_pins.html'));
        assert.ok(html.includes('frontend-flight-computer-source-20261109/source-audit.md'));
        assert.ok(html.includes(bank.identity.specification_sha256));
        assert.doesNotMatch(
          html,
          /<button|<dialog|<canvas|<svg|mailto:|Purchase|Buy now|installed pass/,
        );
      },
    );

    await t.test(
      'inspection integration adds only the scoped source notice and preserves existing controls',
      () => {
        const panel = readFileSync(
          new URL('../src/components/InspectionPanel.tsx', import.meta.url),
          'utf8',
        );
        assert.match(
          panel,
          /<FlightComputerSourceFinding vehicle=\{design\} selectedPart=\{part\}/,
        );
        assert.ok(
          panel.indexOf('<FlightComputerSourceFinding') > panel.indexOf('What this part does'),
        );
        for (const preserved of [
          'Focus in 3D',
          'Isolate part',
          'Hide part',
          '<HighGBoardDetail',
          '<ComponentDepthAccess',
          '<InspectionGeometryAccess',
          '<InspectionStepAccess',
        ])
          assert.ok(panel.includes(preserved), preserved);
      },
    );
  } finally {
    await vite.close();
  }
});
