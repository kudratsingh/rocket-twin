import { lazy, Suspense, useEffect, useMemo, useState } from 'react';
import type { InspectionDocument } from '../types';
import { loadTemplateRegistry, sourceLink, templateLabel, templateValue } from './templateBank';
import type { PartTemplate, TemplateRegistry } from './templateBank';
import { localTemplateRepresentation } from './templateGeometry';
import './templateBank.css';

const LocalTemplatePreview = lazy(() => import('./LocalTemplatePreview'));

export function TemplateRecipeDetail({
  recipe,
  registry,
  onInspect,
}: {
  recipe: PartTemplate;
  registry: TemplateRegistry;
  onInspect: (partId: string) => void;
}) {
  const [parameter, setParameter] = useState<string | null>(null);
  const features = registry.feature_sources.filter((row) => row.template_id === recipe.id);
  const representation = useMemo(
    () => localTemplateRepresentation(recipe, registry),
    [recipe, registry],
  );
  return (
    <article className="template-detail">
      <span className="parts-bank-eyebrow">
        Named source recipe · {templateLabel(recipe.family)}
      </span>
      <h2>{recipe.label}</h2>
      <p className="template-status">
        {recipe.geometry.local_recipe_supported
          ? 'Nominal local geometry recipe supported'
          : 'Local geometry recipe blocked'}
        <span> · installed engineering evidence remains open</span>
      </p>
      <p>{recipe.reuse.reason}</p>
      <div className="template-actions">
        {recipe.source_part_ids.map((partId) => (
          <button key={partId} type="button" onClick={() => onInspect(partId)}>
            Inspect installed {partId}
          </button>
        ))}
      </div>
      <p className="parts-bank-note">
        The installed joint STEP uses assembled nose-datum coordinates. It is not this local
        template, and this catalog does not execute CAD or add a part to the rocket.
      </p>
      {representation && (
        <Suspense fallback={<p role="status">Opening local CAD preview…</p>}>
          <LocalTemplatePreview representation={representation} />
        </Suspense>
      )}
      <section>
        <h3>Recorded parameters</h3>
        <p>Select a parameter to identify its source features. Values are recorded nominals.</p>
        <div className="template-parameter-list">
          {recipe.parameters.map((row) => (
            <button
              key={row.key}
              type="button"
              aria-pressed={parameter === row.key}
              onClick={() => setParameter(parameter === row.key ? null : row.key)}
            >
              <span>{templateLabel(row.key)}</span>
              <strong>{templateValue(row)}</strong>
              <small>
                {row.value_basis.replaceAll('_', ' ')} · tolerance{' '}
                {row.tolerance === null
                  ? 'unavailable'
                  : `±${row.tolerance.plus_minus} ${row.tolerance.unit} (proposed cut)`}
              </small>
            </button>
          ))}
        </div>
      </section>
      <section>
        <h3>Features and connections</h3>
        <p>
          Nominal geometry identifies a surface; contact stiffness and joint capacity stay separate.
        </p>
        <div className="template-feature-list">
          {features.map((feature) => (
            <div
              key={feature.id}
              className={
                parameter && feature.parameter_keys.includes(parameter) ? 'highlighted' : ''
              }
            >
              <strong>{feature.label}</strong>
              <span>
                {templateLabel(feature.kind)} · {feature.status.replaceAll('_', ' ')}
              </span>
              <span>
                Linked parts: {feature.mating_part_ids.join(', ') || 'No recorded mating part'}
                {' · '}installed contact: {feature.installed_contact_status}
              </span>
              <a href={sourceLink(feature.source)} target="_blank" rel="noreferrer">
                {feature.source.path} · {feature.source.locator}
              </a>
            </div>
          ))}
        </div>
      </section>
      <section>
        <h3>Frames and accounting</h3>
        <dl className="parts-bank-dimensions">
          <div>
            <dt>Local units / origin</dt>
            <dd>
              {recipe.local_frame.units} / {recipe.local_frame.origin}
            </dd>
          </div>
          <div>
            <dt>Local axes</dt>
            <dd>{recipe.local_frame.axes}</dd>
          </div>
          <div>
            <dt>Material</dt>
            <dd>{recipe.material}</dd>
          </div>
          <div>
            <dt>Mass ownership</dt>
            <dd>{recipe.mass_accounting.source_part_ids.join(', ')}</dd>
          </div>
          <div>
            <dt>Extra template mass</dt>
            <dd>None charged; source mass is counted once</dd>
          </div>
          <div>
            <dt>Separate local asset</dt>
            <dd>
              {representation ? 'Source-nominal local STEP and GLB' : 'Unavailable · recipe only'}
            </dd>
          </div>
        </dl>
        {recipe.installed_references.map((reference) => (
          <p key={reference.source_part_id} className="parts-bank-note">
            {reference.source_part_id} installed reference: {reference.front_station_mm} mm from
            nose · {reference.cad_frame}. STEP SHA {reference.step.sha256.slice(0, 12)}…
          </p>
        ))}
      </section>
      <section>
        <h3>Parameter sources</h3>
        <ul className="template-sources">
          {recipe.parameters.map((row) => (
            <li key={row.key}>
              <a href={sourceLink(row.source)} target="_blank" rel="noreferrer">
                {templateLabel(row.key)} · {row.source.path}
              </a>
              <span>
                {row.source.locator} · SHA {row.source.sha256.slice(0, 12)}…
              </span>
              {row.tolerance && (
                <span>
                  Tolerance: {row.tolerance.basis.replaceAll('_', ' ')} ·{' '}
                  {row.tolerance.source.locator}
                </span>
              )}
            </li>
          ))}
        </ul>
      </section>
    </article>
  );
}

export default function TemplateBankPanel({
  vehicle,
  onInspect,
}: {
  vehicle: InspectionDocument;
  onInspect: (partId: string) => void;
}) {
  const [registry, setRegistry] = useState<TemplateRegistry | null>(null);
  const [error, setError] = useState('');
  const [selected, setSelected] = useState('rp1-template:continuous-fin-tab');
  useEffect(() => {
    const abort = new AbortController();
    setRegistry(null);
    setError('');
    loadTemplateRegistry(vehicle, fetch, abort.signal)
      .then((value) => {
        if (!abort.signal.aborted) setRegistry(value);
      })
      .catch((reason: unknown) => {
        if (!abort.signal.aborted)
          setError(reason instanceof Error ? reason.message : 'Template contract unavailable.');
      });
    return () => abort.abort();
  }, [vehicle]);
  const recipe = registry?.templates.find((row) => row.id === selected) ?? registry?.templates[0];
  return (
    <section className="template-bank" aria-label="RP1 named template recipes">
      <header>
        <span className="parts-bank-eyebrow">Parts bank · templates & feature sources</span>
        <h1>Understand what can be reused</h1>
        <p>
          Source-pinned nominal recipes, connection features and missing evidence. Prepared source
          contract · read only · no draft admission.
        </p>
      </header>
      {error ? (
        <p role="alert" className="parts-bank-state parts-bank-error">
          {error}
        </p>
      ) : !registry ? (
        <p role="status" className="parts-bank-state">
          Verifying the prepared template contract…
        </p>
      ) : (
        <>
          <div className="template-workarea">
            <nav aria-label="Named template recipes">
              {registry.templates.map((row) => (
                <button
                  key={row.id}
                  type="button"
                  aria-pressed={recipe?.id === row.id}
                  onClick={() => setSelected(row.id)}
                >
                  <strong>{row.label}</strong>
                  <span>
                    {row.geometry.local_recipe_supported
                      ? 'Nominal recipe'
                      : 'Source gap · blocked'}
                  </span>
                  <small>{row.source_part_ids.join(' + ')}</small>
                </button>
              ))}
              <p>
                {registry.dispositions.length} source records accounted for. Allowances do not
                become solids.
              </p>
            </nav>
            {recipe && (
              <TemplateRecipeDetail
                key={recipe.id}
                recipe={recipe}
                registry={registry}
                onInspect={onInspect}
              />
            )}
          </div>
          <footer>
            No replacement mass is credited and no new hardware is counted. Product conflicts,
            installed flexibility, recovery, thermal and flutter qualification remain open.
          </footer>
        </>
      )}
    </section>
  );
}
