import type { InspectionDocument } from '../types';
import { RP1_CONNECTION_PART_IDS, rp1ConnectionDesignHref } from './rp1Connections.ts';

export const RP1_ASSEMBLY_CONFIGURATION = 'G80-F2-RP1-AD1-definition-v2';
export const RP1_ASSEMBLY_SPECIFICATION =
  '811b3bed631fe2ce30a6b0211beecb739d40ebbbcb10e063f6beba0854631660';
export const RP1_ASSEMBLY_SOURCE_COMMIT = '2308648ecd2c4dbce857350316088524c10986ec';
const DEFINITION = 'e9db49f2cafc89b1f77bf9d7396434297bc8bb8754085fdcf74d3b0242012555';
const RECORD = 'bc349a24fe1cfaa4d883b9e00dc5b75387638a7be5cd4b05d9f32112ee8bd95b';
const GEOMETRY = '238d01e5e3381560aab9eb99673617803ab020e01a8cf171ba4dffe67228b608';
export type AssemblyPartId = (typeof RP1_CONNECTION_PART_IDS)[number];
export const ASSEMBLY_SOURCES = {
  specification: {
    path: 'configs/vehicle/candidates/g80-f2-rp1-ad1-v2.yaml',
    sha256: RP1_ASSEMBLY_SPECIFICATION,
  },
  definition: { path: 'configs/studies/rp1-attachment-definition-v2.yaml', sha256: DEFINITION },
  record: { path: 'runs/wo03-rp1-attachment-definition-20261103-v2/record.json', sha256: RECORD },
  attachment: {
    path: 'docs/wo03-rp1-attachment-definition.md',
    sha256: '012cd168e03807460debd5bb9dbc543f058d02597f87bd83945a769794a1aa4a',
  },
  decision: {
    path: 'docs/wo03-rp1-load-attachment-decision.md',
    sha256: 'af6eabd641063d262d0190ee46f5bbc847e54af5c7a3a1f1c442f0a57740bb47',
  },
} as const;
export type AssemblySourceId = keyof typeof ASSEMBLY_SOURCES;
export interface AssemblyCitation {
  source: AssemblySourceId;
  locator: string;
}
export interface AssemblyNode {
  id: string;
  label: readonly string[];
  x: number;
  y: number;
  parts: readonly AssemblyPartId[];
  note: string;
}
// These are reading-layout coordinates, not vehicle coordinates or new CAD.
export const ASSEMBLY_NODES: readonly AssemblyNode[] = [
  {
    id: 'junction',
    label: ['Outside junction', 'and sewn loops'],
    x: 18,
    y: 54,
    parts: ['shock_cord', 'recovery_connectors', 'nose_recovery_eye', 'parachute'],
    note: 'Intact factory nylon loops meet the leader eye outside the mouth. The nose is a separate branch at the provisional distal junction; no equal load split is credited.',
  },
  {
    id: 'mouth',
    label: ['Body mouth', 'and lip guard'],
    x: 235,
    y: 54,
    parts: ['body', 'rp1_lip_guard', 'recovery_protection'],
    note: 'The accessible junction is brought outside the mouth for service. The guard and canopy blanket are separate counted protection, not qualified anchors or thermal passes.',
  },
  {
    id: 'sleeve',
    label: ['Folded aramid', 'inspection sleeve'],
    x: 452,
    y: 54,
    parts: ['ad1_cord_sleeve'],
    note: 'The 80 mm sleeve occupies stations 980–1060 mm, ahead of the forward ring. It may slide for inspection while accessible; it must not occupy the 4.5 mm notch.',
  },
  {
    id: 'notch',
    label: ['Forward ring', 'rounded notch'],
    x: 669,
    y: 54,
    parts: ['forward_ring', 'rp1_notch_sealer'],
    note: 'The proposed passage is a rounded/sealed U-notch at 60°. Nominal clearance is not a checked moving-rope passage, bend limit or thermal/chafe result.',
  },
  {
    id: 'choker',
    label: ['Leader choker', 'and knot reservation'],
    x: 886,
    y: 54,
    parts: ['rp1_kevlar_wrap', 'rp1_wrap_lock_bond'],
    note: 'A proposed figure-eight-on-a-bight eye is reeved around the tube. The reserved knot box is not actual knot CAD. Working cord/knot must remain free of epoxy or CA; process allowance is not capacity.',
  },
  {
    id: 'aft',
    label: ['Aft ring', 'and tab-end bond'],
    x: 18,
    y: 250,
    parts: ['aft_ring', 'c1_aft_bond_fill', 'ring_bonds'],
    note: 'The aft ring stays off for root/route/cure inspection. Its nominal 0.4 mm tab-end gap is an adhesive joint, not direct butt contact or a hard stop.',
  },
  {
    id: 'gussets',
    label: ['External gussets', 'and body fillets'],
    x: 235,
    y: 250,
    parts: ['root_gussets', 'outer_fin_fillets', 'root_extra_bond_finish'],
    note: 'Source wedges need curved body saddles and finite bonds. No load-sharing fraction, rigid support or mass-removal credit is established.',
  },
  {
    id: 'tabs',
    label: ['Integral fin/tab', 'and internal bonds'],
    x: 452,
    y: 250,
    parts: ['fin_set', 'fin_tabs', 'fin_internal_bonds', 'ad1_slot_fill'],
    note: 'The panel/tab is one continuous blank with separately counted source mass rows. Internal fillets, slots and aft-end adhesive are not a qualified installed root.',
  },
  {
    id: 'body',
    label: ['Continuous body', 'and ring bonds'],
    x: 669,
    y: 250,
    parts: ['body', 'ring_bonds', 'c1_forward_root_bond_fill'],
    note: 'Ring perimeter and bore bonds connect finite paper/wood structures. The forward ring is ahead of the tabs; no direct front-tab support or perfect clamp is credited.',
  },
  {
    id: 'mount',
    label: ['Motor tube', 'and anchor contact'],
    x: 886,
    y: 250,
    parts: ['motor_tube', 'mount_external_shield'],
    note: 'The choker bears just aft of the forward ring. Cord contact, tube ovalization, local ring bending and actual reaction partition remain unknown.',
  },
  {
    id: 'motor',
    label: ['Motor removal', 'and retainer access'],
    x: 886,
    y: 426,
    parts: ['motor', 'motor_retainer', 'retainer_adhesive'],
    note: 'The source preserves an unobstructed bore and independent retainer. Exact motor/tube/retainer/liner seats and product identity remain unresolved; no installed removal or fit pass is claimed.',
  },
];
export const ASSEMBLY_EDGES = [
  {
    id: 'junction-mouth',
    from: 'junction',
    to: 'mouth',
    label: 'Leader/junction service route',
    d: 'M213 101 H235',
  },
  {
    id: 'mouth-sleeve',
    from: 'mouth',
    to: 'sleeve',
    label: 'Leader inside body to sleeve',
    d: 'M430 101 H452',
  },
  {
    id: 'sleeve-notch',
    from: 'sleeve',
    to: 'notch',
    label: 'Sleeve ends before bare rounded notch',
    d: 'M647 101 H669',
  },
  {
    id: 'notch-choker',
    from: 'notch',
    to: 'choker',
    label: 'Bare leader passage to choker',
    d: 'M864 101 H886',
  },
  {
    id: 'choker-mount',
    from: 'choker',
    to: 'mount',
    label: 'Choker/tube contact; capacity unknown',
    d: 'M983 148 V250',
  },
  {
    id: 'mount-motor',
    from: 'mount',
    to: 'motor',
    label: 'Bore/removal access must remain unobstructed',
    d: 'M983 344 V426',
  },
] as const;
export interface AssemblyStep {
  id: string;
  title: string;
  stage: 'construction concept' | 'service concept';
  nodes: readonly string[];
  summary: string;
  checks: readonly string[];
  limit: string;
  citations: readonly AssemblyCitation[];
}
export const ASSEMBLY_STEPS: readonly AssemblyStep[] = [
  {
    id: 'source-stock',
    title: 'Stock, notch and witness preparation',
    stage: 'construction concept',
    nodes: ['notch', 'body', 'mount', 'tabs', 'gussets'],
    summary:
      'The recorded article sequence starts with labelled stock, dimensions, ply direction, conditioned bond process and witness marks before inaccessible assembly.',
    checks: [
      'The proposed notch is rounded and sealed before the route is buried; the source radius is intent, not an established exact-cord bend limit.',
      'Actual bore, stock and bond thickness need documentation. Generic nominal dimensions and existing mass reserves do not establish incoming acceptance.',
    ],
    limit:
      'This is a reading of a sacrificial test/construction concept, not authority to cut, bond, purchase or manufacture the flight rocket.',
    citations: [
      { source: 'attachment', locator: '§2 Assembly/inspection sequence, item 1' },
      { source: 'definition', locator: 'route; test_article.material_and_bonds' },
    ],
  },
  {
    id: 'dry-route',
    title: 'Dry-route the leader and intact loops',
    stage: 'construction concept',
    nodes: ['junction', 'mouth', 'notch', 'choker', 'mount'],
    summary:
      'The proposed leader has figure-eight-on-a-bight eyes: a proximal choker around the tube and a distal loop-to-loop hitch to the uncut nylon factory loop.',
    checks: [
      'The knot reservation lies between fins at 60°. The box is a clearance reservation, not a reconstructed dressed knot or a proof against migration.',
      'The source reserves 300 mm of raw leader at each end, including 100 mm minimum tails. If actual dressing consumes more, tails cannot be shortened to force a reach pass.',
      'The nylon remains uncut with both original sewn loops. Nominal length, sewing, finished mass, seating/slip and completed termination capacity remain unverified.',
    ],
    limit:
      'Advertised raw-rope tensile labels are not finished knot/loop allowables. No knot efficiency, equal leg sharing or approved termination is credited.',
    citations: [
      { source: 'attachment', locator: '§1 Exact products/finished ends; §2 sequence item 2' },
      { source: 'definition', locator: 'cord.kevlar; cord.nylon' },
    ],
  },
  {
    id: 'protection',
    title: 'Protection and inspection access',
    stage: 'construction concept',
    nodes: ['mouth', 'sleeve', 'notch', 'choker'],
    summary:
      'The corrected sleeve lies ahead of the forward ring, leaving the notch bare. The lip guard and canopy blanket remain distinct protection allocations.',
    checks: [
      'The 80 mm folded aramid sleeve spans 980–1060 mm and must not occupy the 4.5 mm notch. The earlier through-notch sleeve arrangement was rejected.',
      'Loose textile ties permit sleeve movement for inspection while accessible. Working cord and knot receive no epoxy or CA.',
      'The source calls for recording dressed topology, knot/fin/body clearances and external junction reach before ring bonds or inaccessible closure.',
    ],
    limit:
      'Textile finish, fold/tie packing, actual clearances and thermal/chafe performance are unknown. Protection budgets carry no structural capacity.',
    citations: [
      { source: 'attachment', locator: '§2 Connection/protection/service; sequence item 2' },
      { source: 'definition', locator: 'route.heat_abrasion_sleeve' },
    ],
  },
  {
    id: 'forward-root',
    title: 'Forward mount and integral root concept',
    stage: 'construction concept',
    nodes: ['notch', 'mount', 'body', 'tabs', 'gussets', 'aft'],
    summary:
      'The recorded order bonds the forward ring to the mount, introduces the assembly through body access, then adds integral fin/tab blanks and continuous root joints.',
    checks: [
      'The forward ring is ahead of the tabs, not a direct front-tab support. Tab/mount fillets, external gussets/body saddles, body slot edges and aft-end adhesive form finite routes.',
      'Gusset undersides must correspond to the curved body in the proposed construction; flat stock is not a verified saddle.',
      'The nominal 0.4 mm aft tab/ring gap needs an adhesive joint; there is no direct butt contact or perfect clamp. Existing adhesive allocations stay counted once.',
    ],
    limit:
      'AD1’s optimistic wood-panel screen fails before complete root flexibility is included. Installed joint strength/movement and peel/flutter remain unavailable; D1 admits no new construction.',
    citations: [
      { source: 'attachment', locator: '§2 sequence item 3; §3 Changed fin support' },
      { source: 'decision', locator: '§2 Complete attachment model; §3 Material decision' },
      { source: 'definition', locator: 'fin_joints.support' },
    ],
  },
  {
    id: 'open-inspection',
    title: 'Inspect route and cure witnesses before closure',
    stage: 'construction concept',
    nodes: ['aft', 'tabs', 'gussets', 'body', 'notch', 'choker'],
    summary:
      'The aft ring remains off until the tab fillets, harness route and cure witnesses have been inspected.',
    checks: [
      'The source retains the opening so internal bonds and the leader route can be documented before direct sight is lost.',
      'Later inspection uses the aft opening and body mouth, with a borescope where direct sight is lost.',
      'A cure witness is an inspection requirement; the source does not supply a universally qualified cure schedule, acceptance signature or hidden-joint capacity.',
    ],
    limit:
      'Advancing this reading step records no inspection completion. Closure and physical work require their existing separate authorization and evidence.',
    citations: [
      { source: 'attachment', locator: '§2 Assembly/inspection sequence, items 3–4' },
      { source: 'specification', locator: 'parts[id=fin_internal_bonds]; parts[id=ring_bonds]' },
    ],
  },
  {
    id: 'aft-motor',
    title: 'Aft bond and motor removal access',
    stage: 'construction concept',
    nodes: ['aft', 'tabs', 'body', 'mount', 'motor'],
    summary:
      'After the recorded open inspection, the concept adds aft ring/bonds and retains inspection from the aft opening and body mouth.',
    checks: [
      'The motor bore and independent retainer remain unobstructed in the source intent. The anchor/protection route does not establish an actual motor removal trial.',
      'Exact case, tube, retainer, liner termination and hot-clearance/seat correspondence remain separate source and fit holds.',
      'The generic retainer envelope is not adoption of either unresolved product name or a detailed thread/cap model.',
    ],
    limit:
      'No motor installation/removal, supplier fit, hot clearance or independent retention pass is established by this schematic.',
    citations: [
      { source: 'attachment', locator: '§2 Assembly/inspection sequence, item 4' },
      { source: 'specification', locator: 'parts[id=motor_retainer]; parts[id=motor_tube]' },
      { source: 'decision', locator: '§5 Thermal/recovery/exact motor/retainer gates' },
    ],
  },
  {
    id: 'service-retire',
    title: 'Accessible nylon service; buried anchor retirement',
    stage: 'service concept',
    nodes: ['junction', 'mouth', 'sleeve', 'choker', 'mount', 'notch'],
    summary:
      'The junction is brought outside the mouth to separate/replace the nylon and inspect sewn ends, eyes, tails, guard and canopy pack.',
    checks: [
      'The permanently buried motor-tube choker cannot be replaced without destructive access. This is not a fully replaceable anchor architecture.',
      'Suspected hidden damage retires that assembly in the source service concept; inspection access remains limited.',
      'At the distal junction the nose is a separate branch. Tautening/slack/snags can load one path first; no half-force or equal branch/bond sharing is assumed.',
    ],
    limit:
      'Finished cord/loop/knot strength, bend/chafe/thermal behavior, junction hardware and installed recovery capacity remain unknown. This walkthrough releases no physical service or flight action.',
    citations: [
      {
        source: 'attachment',
        locator: '§2 Recovery force route; Assembly/inspection sequence, item 5',
      },
      { source: 'definition', locator: 'cord.nylon.finished_capacity_N; route' },
      { source: 'record', locator: 'recovery_connections; cord_geometry' },
    ],
  },
];

export function matchesAssemblySource(vehicle: InspectionDocument): boolean {
  const identity = vehicle.identity;
  const ids = vehicle.parts.map((part) => part.id);
  return (
    vehicle.id === RP1_ASSEMBLY_CONFIGURATION &&
    identity?.configuration_id === RP1_ASSEMBLY_CONFIGURATION &&
    identity.specification_sha256 === RP1_ASSEMBLY_SPECIFICATION &&
    identity.definition_sha256 === DEFINITION &&
    identity.record_sha256 === RECORD &&
    identity.inspection_geometry_sha256 === GEOMETRY &&
    ids.length === 55 &&
    new Set(ids).size === 55 &&
    RP1_CONNECTION_PART_IDS.every((id) => ids.includes(id))
  );
}
export function assemblyStep(id: string): AssemblyStep | null {
  return ASSEMBLY_STEPS.find((step) => step.id === id) ?? null;
}
export function assemblyNode(id: string): AssemblyNode | null {
  return ASSEMBLY_NODES.find((node) => node.id === id) ?? null;
}
export function assemblySourceHref(source: AssemblySourceId): string {
  return `https://github.com/kudratsingh/rocket-twin/blob/${RP1_ASSEMBLY_SOURCE_COMMIT}/${ASSEMBLY_SOURCES[source].path}`;
}
export interface Rp1AssemblyDesignTarget {
  partId: AssemblyPartId;
  href: string;
  configurationId: typeof RP1_ASSEMBLY_CONFIGURATION;
  specificationSha256: typeof RP1_ASSEMBLY_SPECIFICATION;
}
export function assemblyDesignTarget(
  vehicle: InspectionDocument,
  partId: string,
): Rp1AssemblyDesignTarget | null {
  if (
    !matchesAssemblySource(vehicle) ||
    !(RP1_CONNECTION_PART_IDS as readonly string[]).includes(partId)
  )
    return null;
  return {
    partId: partId as AssemblyPartId,
    href: rp1ConnectionDesignHref(partId),
    configurationId: RP1_ASSEMBLY_CONFIGURATION,
    specificationSha256: RP1_ASSEMBLY_SPECIFICATION,
  };
}
