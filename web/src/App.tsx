import { lazy, Suspense, useCallback, useEffect, useState } from 'react';
import { getJson } from './api';
import { InspectionPanel } from './components/InspectionPanel';
import { Icon } from './components/Icons';
import { PartsTree } from './components/PartsTree';
import { Viewer } from './components/Viewer';
import { useInspection } from './store';
import type { Catalog, InspectionDocument, MassSample } from './types';

import {
  inspectionSourceContext,
  requireInspectionSource,
  drawingShortcut,
} from './workspaces/inspectionWorkflow';
import { DesignVisual } from './workspaces/DesignVisual';
import { InspectionWorkspace } from './workspaces/InspectionWorkspace';
import {
  WorkspaceFrame,
  WorkspaceNavigation,
  WorkspaceIdentityStrip,
} from './workspaces/WorkspaceChrome';
import { readWorkspace, workspaceHref, designHref } from './workspaces/navigation';

import { readPartLink, partHref } from './workspaces/partLinks';

function currentHref() {
  return typeof window === 'undefined'
    ? '/'
    : `${window.location.pathname}${window.location.search}${window.location.hash}`;
}

const Experiment = lazy(() => import('./experiments/Experiment'));
const AnalysisWorkspace = lazy(() => import('./analysis/AnalysisWorkspace'));
const EngineeringWorkbench = lazy(() => import('./workbench/EngineeringWorkbench'));

export default function App() {
  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [vehicleId, setVehicleId] = useState(
    () =>
      new URL(currentHref(), 'http://local.invalid').searchParams.get('design') ||
      'G80-F2-RP1-AD1-definition-v2',
  );
  const [loadedVehicle, setVehicle] = useState<InspectionDocument | null>(null);
  const vehicle = loadedVehicle?.id === vehicleId ? loadedVehicle : null;
  const [catalogError, setCatalogError] = useState('');
  const [vehicleError, setVehicleError] = useState('');
  const [massError, setMassError] = useState('');
  const [mass, setMass] = useState<MassSample | null>(null);
  const [burn, setBurn] = useState(0);
  const [massLoading, setMassLoading] = useState(false);
  const [href, setHref] = useState(currentHref);
  const route = readWorkspace(new URL(href, 'http://local.invalid').search);
  const mode = route.workspace;
  const navigate = useCallback((next: string) => {
    if (currentHref() !== next) window.history.pushState(null, '', next);
    setHref(currentHref());
  }, []);
  const changeConfiguration = useCallback(
    (id: string) => {
      setVehicleId(id);
      navigate(designHref(currentHref(), id));
    },
    [navigate],
  );
  useEffect(() => {
    const changed = () => setHref(currentHref());
    window.addEventListener('popstate', changed);
    return () => window.removeEventListener('popstate', changed);
  }, []);
  useEffect(() => {
    if (!catalog) return;
    const requested = new URL(href, 'http://local.invalid').searchParams.get('design');
    setVehicleId(requested || catalog.default_design_id || 'G80-F2-RP1-AD1-definition-v2');
  }, [href, catalog]);
  const [retry, setRetry] = useState(0);
  const resetVehicle = useInspection((s) => s.resetVehicle);

  useEffect(() => {
    const controller = new AbortController();
    setCatalogError('');
    void getJson<Catalog>('/api/vehicles', controller.signal)
      .then((data) => {
        if (controller.signal.aborted) return;
        setCatalog(data);
        setVehicleId(
          (id) => id || data.vehicles.find((entry) => entry.available !== false)?.id || '',
        );
      })
      .catch((error: unknown) => {
        if (!controller.signal.aborted)
          setCatalogError(
            error instanceof Error ? error.message : 'Could not load vehicle catalog.',
          );
      });
    return () => controller.abort();
  }, [retry]);

  useEffect(() => {
    if (!vehicleId) return;
    const controller = new AbortController();
    setVehicle(null);
    setMass(null);
    setBurn(0);
    setVehicleError('');
    setMassError('');
    resetVehicle();
    void getJson<InspectionDocument>(
      `/api/vehicles/${encodeURIComponent(vehicleId)}`,
      controller.signal,
    )
      .then((data) => {
        if (!controller.signal.aborted) setVehicle(requireInspectionSource(data, vehicleId));
      })
      .catch((error: unknown) => {
        if (!controller.signal.aborted)
          setVehicleError(error instanceof Error ? error.message : 'Could not load vehicle.');
      });
    return () => controller.abort();
  }, [vehicleId, retry, resetVehicle]);

  const [partLinkNotice, setPartLinkNotice] = useState<string | null>(null);
  useEffect(() => {
    if (!vehicle || mode !== 'design') return;
    const link = readPartLink(new URL(href, 'http://local.invalid').search, vehicle);
    setPartLinkNotice(link.notice);
    if (link.notice || link.part !== null) useInspection.getState().select(link.part);
    if (link.notice) return;
    return useInspection.subscribe((state, previous) => {
      if (state.selectedId === previous.selectedId) return;
      if (state.selectedId && !vehicle.parts.some((p) => p.id === state.selectedId)) return;
      const next = partHref(currentHref(), vehicle, state.selectedId);
      window.history.replaceState(null, '', next);
      setHref(next);
    });
  }, [vehicle, href, mode]);

  useEffect(() => {
    if (!vehicle) return;
    const controller = new AbortController();
    setMassLoading(true);
    setMass(null);
    setMassError('');
    const timeout = window.setTimeout(() => {
      void getJson<MassSample>(
        `/api/vehicles/${encodeURIComponent(vehicle.id)}/mass?burn_fraction=${burn}`,
        controller.signal,
      )
        .then((data) => {
          if (!controller.signal.aborted) setMass({ ...data, burn_fraction: burn });
        })
        .catch((error: unknown) => {
          if (!controller.signal.aborted) {
            setMass(null);
            setMassError(error instanceof Error ? error.message : 'Mass properties unavailable.');
          }
        })
        .finally(() => {
          if (!controller.signal.aborted) setMassLoading(false);
        });
    }, 100);
    return () => {
      controller.abort();
      window.clearTimeout(timeout);
    };
  }, [vehicle, burn]);

  useEffect(() => {
    function keydown(event: KeyboardEvent) {
      if (event.defaultPrevented || event.ctrlKey || event.metaKey || event.altKey) return;
      if (mode !== 'design' && mode !== 'analysis') return;
      if (
        event.target instanceof HTMLElement &&
        (['INPUT', 'SELECT', 'TEXTAREA'].includes(event.target.tagName) ||
          event.target.isContentEditable)
      )
        return;
      const state = useInspection.getState();
      if (event.key === 'Escape') state.select(null);
      const drawing =
        mode === 'design'
          ? document.querySelector<HTMLElement>('.research-design-visual[data-representation="2d"]')
          : null;
      const drawingAction = drawingShortcut(event.key);
      if (drawing && drawingAction) {
        event.preventDefault();
        if (drawingAction !== 'unsupported')
          drawing
            .querySelector<HTMLButtonElement>(`[data-inspection-action="${drawingAction}"]`)
            ?.click();
        return;
      }
      if (event.key.toLowerCase() === 'r') state.resetCamera();
      if (event.key.toLowerCase() === 'f' && state.selectedId) {
        const selected = vehicle?.parts.find((part) => part.id === state.selectedId);
        if (selected?.mesh_url) {
          if (state.section) state.toggleSection();
          state.focusPart(selected.id);
        }
      }
      if (event.key.toLowerCase() === 'e' && mode === 'design')
        state.setExploded(state.exploded > 0 ? 0 : 1);
      if (event.key.toLowerCase() === 's') state.toggleSection();
      if (event.key === '/') {
        event.preventDefault();
        document.querySelector<HTMLInputElement>('[aria-label="Search parts"]')?.focus();
      }
    }
    window.addEventListener('keydown', keydown);
    return () => window.removeEventListener('keydown', keydown);
  }, [mode, vehicle]);

  const selectedEntry = [...(catalog?.vehicles ?? []), ...(catalog?.candidates ?? [])].find(
    (entry) => entry.id === vehicleId,
  );
  const inspectionContext = inspectionSourceContext(vehicleId, vehicle, selectedEntry);
  const inspectionError = vehicleError || (!vehicle ? catalogError : '');
  const constructionNotice = (
    <p className="route-notice">
      Current conventional construction:{' '}
      <a
        href="/?workspace=engineering&view=g80-f2"
        onClick={(event) => {
          if (
            event.button !== 0 ||
            event.metaKey ||
            event.ctrlKey ||
            event.shiftKey ||
            event.altKey
          )
            return;
          event.preventDefault();
          navigate('/?workspace=engineering&view=g80-f2');
        }}
      >
        open the separate G80-F2 stock-and-joint walkthrough
      </a>
      . The CAD selector contains recorded reference assemblies, not a complete F2 assembly.
    </p>
  );
  return (
    <WorkspaceFrame
      workspace={mode}
      header={
        <header className="topbar">
          <a className="brand" href="/" aria-label="Rocket Twin home">
            <span className="brand-mark">
              <Icon name="rocket" size={23} />
            </span>
            <span>
              ROCKET<span className="brand-light">TWIN</span>
              <small>Engineering workspace</small>
            </span>
          </a>
          <span className="topbar-divider" />
          <div
            className="vehicle-picker"
            style={{ display: mode !== 'design' && mode !== 'analysis' ? 'none' : undefined }}
          >
            <label htmlFor="vehicle">Configuration</label>
            <select
              id="vehicle"
              value={vehicleId}
              onChange={(event) => changeConfiguration(event.target.value)}
              disabled={!catalog}
            >
              {!catalog && (
                <option value={vehicleId}>
                  {vehicleId === 'G80-F2-RP1-AD1-definition-v2'
                    ? 'G80 RP1 / AD1 v2 · source loading'
                    : vehicleId}
                </option>
              )}
              <optgroup label="Current engineering definition · source drawings">
                {catalog?.candidates
                  .filter((entry) => entry.id === 'G80-F2-RP1-AD1-definition-v2')
                  .map((entry) => (
                    <option key={entry.id} value={entry.id} disabled={entry.available === false}>
                      {entry.label || entry.id}
                    </option>
                  ))}
              </optgroup>
              <optgroup label="Archived reference CAD · separate designs">
                {catalog?.vehicles.map((entry) => (
                  <option key={entry.id} value={entry.id} disabled={entry.available === false}>
                    {entry.label || entry.name || entry.id}
                  </option>
                ))}
              </optgroup>
              {!!catalog?.candidates.length && (
                <optgroup label="Historical candidate designs — not adopted">
                  {catalog.candidates
                    .filter((entry) => entry.id !== 'G80-F2-RP1-AD1-definition-v2')
                    .map((entry) => (
                      <option key={entry.id} value={entry.id} disabled={entry.available === false}>
                        {entry.label || entry.name || entry.id}
                      </option>
                    ))}
                </optgroup>
              )}
            </select>
          </div>

          <details className="glossary">
            <summary>Terms & units</summary>
            <div>
              <h3>Plain-English key</h3>
              <dl>
                <dt>CG · centre of gravity</dt>
                <dd>The vehicle’s balance point.</dd>
                <dt>CP · centre of pressure</dt>
                <dd>The model’s aerodynamic force point.</dd>
                <dt>Calibre (cal)</dt>
                <dd>
                  One body diameter; the static margin is the CG-to-CP separation in these units.
                </dd>
                <dt>TVC · thrust vector control</dt>
                <dd>Steering by tilting the motor.</dd>
                <dt>CAD · computer-aided design</dt>
                <dd>The source geometry; the display mesh is a tessellation of that geometry.</dd>
                <dt>FEA · finite element analysis</dt>
                <dd>
                  A numerical model of structural response. Convergence is separate from physical
                  validation.
                </dd>
                <dt>FMEA · failure modes and effects analysis</dt>
                <dd>A recorded cause, consequence, mitigation and residual-risk assessment.</dd>
                <dt>IMU · inertial measurement unit</dt>
                <dd>Acceleration and rotation sensors.</dd>
                <dt>PID / RL</dt>
                <dd>
                  Proportional–integral–derivative control / reinforcement learning. Later
                  controller work remains open.
                </dd>
                <dt>HIL · hardware in the loop</dt>
                <dd>Testing real electronics against a simulated vehicle.</dd>
                <dt>NAR / FAA / RSO</dt>
                <dd>
                  National Association of Rocketry / Federal Aviation Administration / Range Safety
                  Officer.
                </dd>
                <dt>g · mm · m · N · N·s</dt>
                <dd>
                  Grams · millimetres · metres · newtons of force · newton seconds of impulse.
                </dd>
                <dt>ASA / G11</dt>
                <dd>
                  Acrylonitrile styrene acrylate print polymer / glass-fibre epoxy laminate.
                  Material and process qualification remain open.
                </dd>
                <dt>SHA-256</dt>
                <dd>A content fingerprint identifying the exact source or geometry record.</dd>
              </dl>
            </div>
          </details>
          <span className="local-badge">
            <span />
            Local workspace
          </span>
        </header>
      }
      navigation={
        <WorkspaceNavigation
          active={mode}
          href={href}
          onNavigate={(_workspace, next) => navigate(next)}
        />
      }
      identity={
        <WorkspaceIdentityStrip
          name={
            mode === 'engineering'
              ? 'Engineering drawings — select the source snapshot below'
              : mode === 'experiments' || mode === 'replay'
                ? 'Preliminary simulated flights — exact identity follows the selected run'
                : inspectionContext.name
          }
          maturity={
            mode === 'engineering'
              ? 'Concept, envelope and local joint drawings; maturity stated per source'
              : mode === 'experiments' || mode === 'replay'
                ? 'Existing Python/JAX model; PID and RL remain later milestones'
                : inspectionContext.maturity
          }
          state={
            mode === 'engineering' || mode === 'experiments' || mode === 'replay'
              ? 'ready'
              : inspectionError
                ? 'unavailable'
                : vehicle
                  ? 'ready'
                  : 'loading'
          }
          details={
            <>
              <p>
                Calculated results, estimated inputs, measured evidence and unavailable coverage
                remain distinct. A successful simulation or displayed geometry does not approve
                construction or flight.
              </p>
              <p>
                {mode === 'design' || mode === 'analysis'
                  ? `Selected identifier: ${vehicleId || 'loading'}.`
                  : 'Configuration, source fingerprints and limitations are attached to the displayed drawing or run.'}
              </p>
              {(mode === 'design' || mode === 'analysis') && (
                <dl className="research-source-fingerprints">
                  <dt>Resolved specification</dt>
                  <dd>
                    {inspectionContext.specification || 'Unavailable for the requested source'}
                  </dd>
                  <dt>Recorded CAD revision</dt>
                  <dd>{inspectionContext.cadRevision || 'Unavailable for the requested source'}</dd>
                  <dt>Geometry coverage</dt>
                  <dd>
                    {vehicle
                      ? `${inspectionContext.meshCount}/${vehicle.parts.length} components have recorded meshes. 2D uses source dimensions and preserves unavailable geometry.`
                      : 'Requested source not loaded.'}
                  </dd>
                </dl>
              )}
            </>
          }
        />
      }
      footer={
        <footer className="app-status">
          <span>Preliminary design · no build or flight release</span>
          <span>
            {mode === 'engineering'
              ? 'Exact source identity and finding state accompany each drawing'
              : mode === 'experiments' || mode === 'replay'
                ? 'Saved runs are separate from the working design · recorded pose only'
                : massError
                  ? `Mass properties unavailable: ${massError}`
                  : massLoading
                    ? 'Updating backend mass properties…'
                    : vehicle
                      ? `${vehicle.parts.length} source-linked parts`
                      : 'Inspection source loading/unavailable'}
          </span>
        </footer>
      }
    >
      {catalogError && vehicle && mode === 'analysis' && (
        <p className="route-notice" role="status">
          Configuration list unavailable: {catalogError}. The displayed source document is loaded
          independently.
        </p>
      )}
      {route.notice && (
        <p className="route-notice" role="status">
          {route.notice}
        </p>
      )}
      {mode === 'engineering' ? (
        <Suspense
          fallback={
            <main className="center-state" role="status">
              Loading engineering walkthrough…
            </main>
          }
        >
          <EngineeringWorkbench />
        </Suspense>
      ) : mode === 'experiments' || mode === 'replay' ? (
        <Suspense
          fallback={
            <main className="center-state" role="status">
              Loading experiments and recorded flights…
            </main>
          }
        >
          <Experiment
            configurationId={vehicleId}
            vehicle={vehicle}
            onConfigurationChange={changeConfiguration}
            workspace={mode}
            onOpenReplay={() => navigate(workspaceHref(currentHref(), 'replay'))}
          />
        </Suspense>
      ) : inspectionError ? (
        <main className="center-state">
          <h1>Selected inspection source unavailable</h1>
          <p>{inspectionError}</p>
          <p>
            Engineering drawings and saved experiments remain independently available. Start the
            local Python API on port 8000 to load inspection data.
          </p>
          <button className="primary-button" onClick={() => setRetry((n) => n + 1)}>
            Retry inspection source
          </button>
        </main>
      ) : !vehicle ? (
        <main className="center-state" role="status">
          <span className="spinner" />
          <h1>Loading resolved configuration</h1>
          <p className="muted">Retrieving specification, CAD identity and recorded evidence…</p>
        </main>
      ) : mode === 'analysis' ? (
        <Suspense
          fallback={
            <main className="center-state" role="status">
              <span className="spinner" />
              Loading recorded analysis workspace…
            </main>
          }
        >
          <AnalysisWorkspace
            key={vehicle.id}
            vehicle={vehicle}
            candidateMessage={catalog?.candidate_message}
          />
        </Suspense>
      ) : (
        <InspectionWorkspace
          source={
            <>
              {partLinkNotice && <p role="alert">{partLinkNotice}</p>}
              {constructionNotice}
              {catalogError && (
                <p className="route-notice" role="status">
                  Configuration list unavailable: {catalogError}. The displayed source document is
                  loaded independently.
                </p>
              )}
            </>
          }
          tree={
            <>
              <PartsTree
                key={`parts-${vehicle.id}`}
                parts={vehicle.parts}
                candidateMessage={catalog?.candidate_message}
              />
            </>
          }
          visual={
            <>
              <DesignVisual
                key={vehicle.id}
                vehicle={vehicle}
                meshView={
                  <Viewer
                    key={`viewer-${vehicle.id}`}
                    vehicle={vehicle}
                    mass={mass}
                    burn={burn}
                    onBurnChange={setBurn}
                  />
                }
              />
            </>
          }
          inspector={
            <>
              <InspectionPanel key={`inspector-${vehicle.id}`} vehicle={vehicle} mass={mass} />
            </>
          }
        />
      )}
    </WorkspaceFrame>
  );
}
