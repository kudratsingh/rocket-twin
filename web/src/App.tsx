import { lazy, Suspense, useEffect, useState } from 'react';
import { getJson } from './api';
import { InspectionPanel } from './components/InspectionPanel';
import { Icon } from './components/Icons';
import { PartsTree } from './components/PartsTree';
import { Viewer } from './components/Viewer';
import { useInspection } from './store';
import type { Catalog, InspectionDocument, MassSample } from './types';

type Mode = 'inspect' | 'analysis' | 'experiment' | 'workbench';
const Experiment = lazy(() => import('./experiments/Experiment'));
const AnalysisWorkspace = lazy(() => import('./analysis/AnalysisWorkspace'));
const EngineeringWorkbench = lazy(() => import('./workbench/EngineeringWorkbench'));

export default function App() {
  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [vehicleId, setVehicleId] = useState('');
  const [vehicle, setVehicle] = useState<InspectionDocument | null>(null);
  const [catalogError, setCatalogError] = useState('');
  const [vehicleError, setVehicleError] = useState('');
  const [massError, setMassError] = useState('');
  const [mass, setMass] = useState<MassSample | null>(null);
  const [burn, setBurn] = useState(0);
  const [massLoading, setMassLoading] = useState(false);
  const [mode, setMode] = useState<Mode>(() =>
    typeof window !== 'undefined' &&
    new URLSearchParams(window.location.search).get('workspace') === 'engineering'
      ? 'workbench'
      : 'inspect',
  );
  const [retry, setRetry] = useState(0);
  const resetVehicle = useInspection((s) => s.resetVehicle);

  useEffect(() => {
    const controller = new AbortController();
    setCatalogError('');
    void getJson<Catalog>('/api/vehicles', controller.signal)
      .then((data) => {
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
      .then(setVehicle)
      .catch((error: unknown) => {
        if (!controller.signal.aborted)
          setVehicleError(error instanceof Error ? error.message : 'Could not load vehicle.');
      });
    return () => controller.abort();
  }, [vehicleId, retry, resetVehicle]);

  useEffect(() => {
    if (!vehicle) return;
    const controller = new AbortController();
    setMassLoading(true);
    setMassError('');
    const timeout = window.setTimeout(() => {
      void getJson<MassSample>(
        `/api/vehicles/${encodeURIComponent(vehicle.id)}/mass?burn_fraction=${burn}`,
        controller.signal,
      )
        .then((data) => setMass({ ...data, burn_fraction: burn }))
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
      if (event.ctrlKey || event.metaKey || event.altKey) return;
      if (
        event.target instanceof HTMLElement &&
        (['INPUT', 'SELECT', 'TEXTAREA'].includes(event.target.tagName) ||
          event.target.isContentEditable)
      )
        return;
      const state = useInspection.getState();
      if (event.key === 'Escape') state.select(null);
      if (mode === 'experiment' || mode === 'workbench') return;
      if (event.key.toLowerCase() === 'r') state.resetCamera();
      if (event.key.toLowerCase() === 'f' && state.selectedId) {
        const selected = vehicle?.parts.find((part) => part.id === state.selectedId);
        if (selected?.mesh_url) state.focusPart(selected.id);
      }
      if (event.key.toLowerCase() === 'e' && mode === 'inspect')
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
  return (
    <div className="app-shell">
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
          style={{ display: mode === 'workbench' ? 'none' : undefined }}
        >
          <label htmlFor="vehicle">Configuration</label>
          <select
            id="vehicle"
            value={vehicleId}
            onChange={(event) => setVehicleId(event.target.value)}
            disabled={!catalog}
          >
            <optgroup label="Active integrated designs">
              {catalog?.vehicles.map((entry) => (
                <option key={entry.id} value={entry.id} disabled={entry.available === false}>
                  {entry.label || entry.name || entry.id}
                </option>
              ))}
            </optgroup>
            {!!catalog?.candidates.length && (
              <optgroup label="Candidate designs — not adopted">
                {catalog.candidates.map((entry) => (
                  <option key={entry.id} value={entry.id} disabled={entry.available === false}>
                    {entry.label || entry.name || entry.id}
                  </option>
                ))}
              </optgroup>
            )}
          </select>
        </div>
        <nav className="mode-tabs" aria-label="Workspace mode">
          <button
            className={mode === 'workbench' ? 'active' : ''}
            onClick={() => setMode('workbench')}
          >
            Engineering
          </button>
          <button className={mode === 'inspect' ? 'active' : ''} onClick={() => setMode('inspect')}>
            Inspect
          </button>
          <button
            className={mode === 'analysis' ? 'active' : ''}
            onClick={() => setMode('analysis')}
          >
            Analysis
          </button>
          <button
            className={mode === 'experiment' ? 'active' : ''}
            onClick={() => setMode('experiment')}
          >
            Experiment
          </button>
        </nav>
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
                Proportional–integral–derivative control / reinforcement learning. Later controller
                work remains open.
              </dd>
              <dt>HIL · hardware in the loop</dt>
              <dd>Testing real electronics against a simulated vehicle.</dd>
              <dt>NAR / FAA / RSO</dt>
              <dd>
                National Association of Rocketry / Federal Aviation Administration / Range Safety
                Officer.
              </dd>
              <dt>g · mm · m · N · N·s</dt>
              <dd>Grams · millimetres · metres · newtons of force · newton seconds of impulse.</dd>
              <dt>ASA / G11</dt>
              <dd>
                Acrylonitrile styrene acrylate print polymer / glass-fibre epoxy laminate. Material
                and process qualification remain open.
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
      <div className="acceptance-banner">
        <Icon name="warning" size={15} />
        <strong>Preliminary design — engineering acceptance remains open</strong>
        <span>Calculated models · unqualified hardware · no flight release</span>
      </div>
      <div className="workspace-context">
        <div>
          <span className="context-dot" />
          <strong>
            {mode === 'workbench'
              ? 'G80 / C1 engineering walkthrough'
              : selectedEntry?.label || vehicle?.label || 'Vehicle inspection'}
          </strong>
          <span>
            {mode === 'workbench'
              ? 'Separate preliminary study · linked construction and evidence'
              : selectedEntry?.description || 'Source-linked geometry and evidence'}
          </span>
        </div>
        <span className="context-status">
          {mode === 'workbench'
            ? 'Concept presentation · engineering acceptance open'
            : selectedEntry?.design_status || 'Integrated design · acceptance open'}
        </span>
      </div>
      {mode === 'workbench' ? (
        <Suspense
          fallback={
            <main className="center-state" role="status">
              Loading engineering walkthrough…
            </main>
          }
        >
          <EngineeringWorkbench />
        </Suspense>
      ) : catalogError || vehicleError ? (
        <main className="center-state">
          <Icon name="warning" size={30} />
          <h1>Inspection data unavailable</h1>
          <p>{catalogError || vehicleError}</p>
          <p className="muted">
            Start the local API on port 8000, then retry. Missing or incompatible data is never
            treated as a passing result.
          </p>
          <button className="primary-button" onClick={() => setRetry((count) => count + 1)}>
            Retry connection
          </button>
        </main>
      ) : (vehicle?.snapshot_only || selectedEntry?.group === 'candidate') && mode !== 'inspect' ? (
        <main className="center-state">
          <h1>Snapshot inspection only</h1>
          <p>
            This experimental, unadopted candidate cannot run or replay experiments. Select the
            active G80 reference to run or load saved flights.
          </p>
          <p>No accepted compatible stress or temperature overlay is attached to this snapshot.</p>
        </main>
      ) : mode === 'experiment' ? (
        <Suspense
          fallback={
            <main className="center-state" role="status">
              <span className="spinner" />
              Loading experiment workspace…
            </main>
          }
        >
          <Experiment
            configurationId={vehicleId}
            vehicle={vehicle}
            onConfigurationChange={setVehicleId}
          />
        </Suspense>
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
        <main className="inspection-workspace">
          <PartsTree
            key={`parts-${vehicle.id}`}
            parts={vehicle.parts}
            candidateMessage={catalog?.candidate_message}
          />
          <Viewer
            key={`viewer-${vehicle.id}`}
            vehicle={vehicle}
            mass={mass}
            burn={burn}
            onBurnChange={setBurn}
          />
          <InspectionPanel key={`inspector-${vehicle.id}`} vehicle={vehicle} mass={mass} />
        </main>
      )}
      <footer className="app-status">
        <span>
          <span className={`status-dot ${vehicle ? 'connected' : ''}`} />
          {vehicle
            ? `${vehicle.parts.length} source-linked parts · backend mass properties`
            : 'Waiting for local API'}
        </span>
        <span role="status">
          {massError
            ? `Mass properties unavailable: ${massError}`
            : massLoading
              ? 'Updating burn-state mass properties…'
              : mass
                ? `Balance markers at ${Math.round((mass.burn_fraction || 0) * 100)}% propellant consumed`
                : 'Read-only digital twin'}
        </span>
        <span>{catalog?.candidate_message || 'Candidates are separate from adopted designs'}</span>
      </footer>
    </div>
  );
}
