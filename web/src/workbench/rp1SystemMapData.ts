import { RP1_CONNECTIONS_CONFIGURATION, RP1_CONNECTIONS_SHA256 } from './rp1Connections.ts';

export type SystemMapStatus = 'implemented model' | 'source definition' | 'planned' | 'unavailable';
export type SystemMapMode = 'g80' | 'g12';
export type SystemMapNode = {
  id: string;
  title: string;
  subtitle: string;
  status: SystemMapStatus;
  detail: string;
  signal: string;
  source: string[];
  x: number;
  y: number;
};
export type SystemMapEdge = {
  from: string;
  to: string;
  label: string;
  status: SystemMapStatus;
};

export const RP1_SYSTEM_MAP_CONFIGURATION = RP1_CONNECTIONS_CONFIGURATION;
export const RP1_SYSTEM_MAP_SPEC_SHA256 = RP1_CONNECTIONS_SHA256;

export function matchesRp1SystemMapSource(
  configurationId: string,
  specificationSha256: string | null,
) {
  return (
    configurationId === RP1_SYSTEM_MAP_CONFIGURATION &&
    specificationSha256 === RP1_SYSTEM_MAP_SPEC_SHA256
  );
}

// Edges describe source or model interfaces, not verified installed wiring.
export const SYSTEM_MAPS: Record<
  SystemMapMode,
  { nodes: SystemMapNode[]; edges: SystemMapEdge[] }
> = {
  g80: {
    nodes: [
      {
        id: 'inputs',
        title: 'Configuration inputs',
        subtitle: 'motor, mass, CG, inertia',
        status: 'unavailable',
        detail:
          'The shared simulator accepts a complete vehicle and motor curve. RP1 has missing complete flight/inertia inputs, so this diagram cannot run RP1 flight or infer them from inspection meshes.',
        signal: 'SI mass kg; CG/body frame m; inertia kg·m²',
        source: ['src/sim/inputs.py', 'configs/vehicle/candidates/g80-f2-rp1-ad1-v2.yaml'],
        x: 18,
        y: 42,
      },
      {
        id: 'environment',
        title: 'Environment',
        subtitle: 'gravity, atmosphere, wind',
        status: 'implemented model',
        detail:
          'Deterministic ISA troposphere and wind/gust inputs feed the simulator. These are model disturbances, not measured conditions for a particular flight.',
        signal: 'NED world frame; wind m/s; density kg/m³',
        source: ['src/sim/environment.py'],
        x: 245,
        y: 42,
      },
      {
        id: 'forces',
        title: 'Thrust + aero',
        subtitle: 'motor curve, drag, lift, moments',
        status: 'implemented model',
        detail:
          'Source motor curve and quasi-steady subsonic aerodynamic model form forces and moments. Model validity and unqualified physical inputs remain explicit.',
        signal: 'body-axis forces N; moments N·m',
        source: ['src/sim/aero.py', 'src/sim/tvc.py', 'src/sim/dynamics.py'],
        x: 472,
        y: 42,
      },
      {
        id: 'plant',
        title: '6DOF / RK4 plant',
        subtitle: 'changing mass + attitude',
        status: 'implemented model',
        detail:
          'RK4 integrates six-degree-of-freedom translation and rotation, mass/CG/inertia changes, and launch-guide constraints. Current G80 control is none with gimbal locked.',
        signal: 'NED position m, velocity m/s; body rates rad/s; quaternion wxyz',
        source: ['src/sim/dynamics.py', 'src/sim/protocol.py'],
        x: 699,
        y: 42,
      },
      {
        id: 'telemetry',
        title: 'Recorded telemetry',
        subtitle: 'Parquet truth + modeled channels',
        status: 'implemented model',
        detail:
          'The simulator exports state and sampled sensor channels for experiments and replay. A saved archived run is not an RP1 flight result.',
        signal: 'time s; NED/body quantities in SI; AGL m',
        source: ['src/sim/telemetry.py'],
        x: 926,
        y: 42,
      },
      {
        id: 'sensors',
        title: 'Instrument model',
        subtitle: 'IMU, baro, high-g',
        status: 'implemented model',
        detail:
          'Sampled channels include noise, bias, rate, lag and transport delay. Calibration, installed alignment and estimator truth are not established.',
        signal: 'specific force m/s²; body rate rad/s; baro AGL m',
        source: ['src/sim/sensors.py', 'configs/vehicle/candidates/g80-f2-rp1-ad1-v2.yaml'],
        x: 699,
        y: 197,
      },
      {
        id: 'logging',
        title: 'Flight computer + log',
        subtitle: 'source hardware definition',
        status: 'source definition',
        detail:
          'The RP1 source names the computer, battery and log card roles. Firmware, wiring pins, power transients and physical logging reliability remain unverified.',
        signal: 'source signal/power roles; pin map unavailable',
        source: ['configs/vehicle/candidates/g80-f2-rp1-ad1-v2.yaml', 'firmware/README.md'],
        x: 926,
        y: 197,
      },
      {
        id: 'recovery',
        title: 'Independent recovery',
        subtitle: 'separate controller + 1S power',
        status: 'source definition',
        detail:
          'The RP1 source reserves a separate recovery controller and battery. Simulator apogee/recovery drag is simplified; installed deployment, power isolation and harness behavior remain unqualified.',
        signal: 'event/topology only; exact pins unavailable',
        source: ['configs/vehicle/candidates/g80-f2-rp1-ad1-v2.yaml', 'src/sim/dynamics.py'],
        x: 472,
        y: 197,
      },
    ],
    edges: [
      { from: 'inputs', to: 'environment', label: 'scenario', status: 'implemented model' },
      { from: 'inputs', to: 'forces', label: 'motor curve', status: 'unavailable' },
      { from: 'inputs', to: 'plant', label: 'mass / CG / inertia', status: 'unavailable' },
      { from: 'environment', to: 'forces', label: 'air / wind', status: 'implemented model' },
      { from: 'forces', to: 'plant', label: 'N, N·m', status: 'implemented model' },
      { from: 'plant', to: 'telemetry', label: 'state / SI', status: 'implemented model' },
      { from: 'plant', to: 'sensors', label: 'truth → samples', status: 'implemented model' },
      { from: 'sensors', to: 'logging', label: 'modeled channels', status: 'source definition' },
      { from: 'plant', to: 'recovery', label: 'apogee event', status: 'implemented model' },
    ],
  },
  g12: {
    nodes: [
      {
        id: 'vehicle',
        title: '6DOF plant',
        subtitle: 'shared simulation model',
        status: 'implemented model',
        detail:
          'The shared six-degree-of-freedom plant exists, but a future G12 complete configuration and controller validation are separate. This is not installed on current RP1.',
        signal: 'NED state; body rates; SI',
        source: ['src/sim/dynamics.py', 'docs/work-orders/WO-02-six-dof-sim-validation.md'],
        x: 18,
        y: 42,
      },
      {
        id: 'sense',
        title: 'Sensors',
        subtitle: 'noise, rate, bias, latency',
        status: 'implemented model',
        detail:
          'Preliminary sensor models exist. Calibrated G12 hardware and flight observations are not claimed.',
        signal: 'IMU m/s² + rad/s; baro AGL m',
        source: ['src/sim/sensors.py'],
        x: 245,
        y: 42,
      },
      {
        id: 'estimate',
        title: 'State estimate',
        subtitle: 'WO-06 deliverable',
        status: 'planned',
        detail:
          'An estimator must produce a usable state without relying on simulator truth attitude. No qualified estimator is supplied by this map.',
        signal: 'estimated attitude/state; interface not frozen',
        source: ['docs/work-orders/WO-06-avionics-pid-baseline.md'],
        x: 472,
        y: 42,
      },
      {
        id: 'guide',
        title: 'Guidance / setpoint',
        subtitle: 'mission command',
        status: 'planned',
        detail:
          'Guidance and setpoints remain future control work. The external reference diagram’s predictive guidance and numerical target are not adopted.',
        signal: 'desired attitude/rates; values unavailable',
        source: [
          'docs/work-orders/WO-06-avionics-pid-baseline.md',
          'docs/frontend-design-workbench-v2/reference-set-20261109.md',
        ],
        x: 699,
        y: 42,
      },
      {
        id: 'control',
        title: 'PID → later RL',
        subtitle: 'separate WO-06 / WO-07',
        status: 'planned',
        detail:
          'PID gains are null in the source config; RL is a later separate work order. No controller execution, policy, tuning or performance is established.',
        signal: 'command rad; gains/policy unavailable',
        source: [
          'configs/control/pid.yaml',
          'docs/work-orders/WO-06-avionics-pid-baseline.md',
          'docs/work-orders/WO-07-rl-ascent.md',
        ],
        x: 926,
        y: 42,
      },
      {
        id: 'limits',
        title: 'Limits + abort',
        subtitle: 'safe-state boundary',
        status: 'planned',
        detail:
          'Command, position, rate, torque and abort limits require source and safety validation. A numeric output limit in a draft config is not a qualified physical actuator limit.',
        signal: 'bounded command; physical limits unavailable',
        source: ['configs/control/pid.yaml', 'docs/work-orders/WO-06-avionics-pid-baseline.md'],
        x: 926,
        y: 197,
      },
      {
        id: 'actuator',
        title: 'Servo / TVC',
        subtitle: 'preliminary model only',
        status: 'implemented model',
        detail:
          'The shared simulator has servo lag/delay/speed/deadband and two-axis thrust-vector mapping. Linkage, calibration, torque/current and moving inertia are unverified; current G80 gimbal is locked.',
        signal: 'modeled gimbal angle rad → body force/moment',
        source: ['src/sim/actuators.py', 'src/sim/tvc.py', 'src/sim/protocol.py'],
        x: 699,
        y: 197,
      },
      {
        id: 'power',
        title: 'Power + logging',
        subtitle: 'future hardware verification',
        status: 'planned',
        detail:
          'Power, pin assignments, firmware/HIL and log reliability require their own source and testing. Independent recovery must retain its separate power path.',
        signal: 'wiring/pins unavailable',
        source: ['firmware/README.md', 'docs/work-orders/WO-10-firmware-hil.md'],
        x: 472,
        y: 197,
      },
      {
        id: 'recovery',
        title: 'Independent recovery',
        subtitle: 'separate safety path',
        status: 'source definition',
        detail:
          'The RP1 source defines an independent recovery controller/battery; this is a separate concept from G12 ascent control and no G12 installation is inferred.',
        signal: 'separate event/power boundary',
        source: ['configs/vehicle/candidates/g80-f2-rp1-ad1-v2.yaml'],
        x: 245,
        y: 197,
      },
    ],
    edges: [
      { from: 'vehicle', to: 'sense', label: 'state → samples', status: 'implemented model' },
      { from: 'sense', to: 'estimate', label: 'observations', status: 'planned' },
      { from: 'estimate', to: 'guide', label: 'estimated state', status: 'planned' },
      { from: 'guide', to: 'control', label: 'setpoint', status: 'planned' },
      { from: 'control', to: 'limits', label: 'command', status: 'planned' },
      { from: 'limits', to: 'actuator', label: 'bounded command', status: 'planned' },
      { from: 'actuator', to: 'vehicle', label: 'forces / moments', status: 'implemented model' },
    ],
  },
};

export function systemMapNode(mode: SystemMapMode, id: string): SystemMapNode | null {
  return SYSTEM_MAPS[mode].nodes.find((node) => node.id === id) ?? null;
}
