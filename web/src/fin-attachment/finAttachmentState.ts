import {
  RP1_CONNECTIONS_CONFIGURATION,
  RP1_CONNECTION_PART_IDS,
  RP1_CONNECTIONS_SHA256,
} from '../workbench/rp1Connections';
import type { InspectionDocument } from '../types';

export const FIN_ATTACHMENT_GEOMETRY_REVISION =
  '238d01e5e3381560aab9eb99673617803ab020e01a8cf171ba4dffe67228b608';
export const FIN_ATTACHMENT_DETAIL_REVISION =
  '1b81037624a4a6bd59c5d2b89b053b598d1dffae56e94140d6f899d7d6506c42';
export const FIN_ATTACHMENT_PIECE_IDS = [
  'motor_tube',
  'forward_ring',
  'aft_ring',
  'fin_set',
  'fin_tabs',
  'root_gussets',
  'body',
  'motor',
  'motor_retainer',
] as const;
export const FIN_ATTACHMENT_DIMENSION_IDS = ['tab-thickness', 'slot-width', 'aft-gap'] as const;

export type FinAttachmentPieceId = (typeof FIN_ATTACHMENT_PIECE_IDS)[number];
export type FinAttachmentDimensionId = (typeof FIN_ATTACHMENT_DIMENSION_IDS)[number];
export type FinAttachmentSection = 'assembled' | 'longitudinal' | 'transverse';
export type FinAttachmentDrawing = 'root' | 'loadpath';
export type FinAttachmentVector3 = [number, number, number];
export interface FinAttachmentCameraSnapshot {
  position: FinAttachmentVector3;
  target: FinAttachmentVector3;
  up: FinAttachmentVector3;
  zoom: number;
}
export interface FinAttachmentState {
  section: FinAttachmentSection;
  selectedPieceId: FinAttachmentPieceId | null;
  selectedDimensionId: FinAttachmentDimensionId | null;
  isolatedPieceIds: FinAttachmentPieceId[];
  hiddenPieceIds: FinAttachmentPieceId[];
  partsSidebarOpen: boolean;
  evidenceSidebarOpen: boolean;
  camera: FinAttachmentCameraSnapshot | null;
}
export interface FinAttachmentRoute {
  state: FinAttachmentState;
  originPartId: FinAttachmentPieceId;
  drawing: FinAttachmentDrawing | null;
}

export const initialFinAttachmentState: FinAttachmentState = {
  section: 'assembled',
  selectedPieceId: null,
  selectedDimensionId: null,
  isolatedPieceIds: [],
  hiddenPieceIds: [],
  partsSidebarOpen: true,
  evidenceSidebarOpen: true,
  camera: null,
};

const jointKeys = [
  'finJoint',
  'jointOrigin',
  'jointGeometry',
  'jointDetail',
  'jointSection',
  'jointPiece',
  'jointDimension',
  'jointIsolate',
  'jointHidden',
  'jointParts',
  'jointEvidence',
  'jointDrawing',
] as const;
const sourceKeys = ['workspace', 'design', 'spec', 'part', 'view', 'connection'] as const;

function isPieceId(value: unknown): value is FinAttachmentPieceId {
  return typeof value === 'string' && FIN_ATTACHMENT_PIECE_IDS.some((id) => id === value);
}
export function isFinAttachmentDimensionId(value: unknown): value is FinAttachmentDimensionId {
  return (
    typeof value === 'string' && (FIN_ATTACHMENT_DIMENSION_IDS as readonly string[]).includes(value)
  );
}
function isSection(value: unknown): value is FinAttachmentSection {
  return value === 'assembled' || value === 'longitudinal' || value === 'transverse';
}
function uniquePieces(value: unknown): value is FinAttachmentPieceId[] {
  return Array.isArray(value) && value.every(isPieceId) && new Set(value).size === value.length;
}
function vector3(value: unknown): value is FinAttachmentVector3 {
  return (
    Array.isArray(value) &&
    value.length === 3 &&
    value.every((number) => typeof number === 'number' && Number.isFinite(number))
  );
}

/** Camera values are view state, never measured CAD coordinates or URL parameters. */
export function parseFinAttachmentCameraSnapshot(
  value: unknown,
): FinAttachmentCameraSnapshot | null {
  if (!value || typeof value !== 'object') return null;
  const camera = value as Partial<FinAttachmentCameraSnapshot>;
  if (
    !vector3(camera.position) ||
    !vector3(camera.target) ||
    !vector3(camera.up) ||
    typeof camera.zoom !== 'number' ||
    !Number.isFinite(camera.zoom) ||
    camera.zoom <= 0 ||
    camera.position.every((coordinate, index) => coordinate === camera.target![index]) ||
    camera.up.every((coordinate) => coordinate === 0)
  )
    return null;
  return {
    position: [...camera.position],
    target: [...camera.target],
    up: [...camera.up],
    zoom: camera.zoom,
  };
}

export function validFinAttachmentState(state: FinAttachmentState): boolean {
  return (
    isSection(state.section) &&
    (state.selectedPieceId === null || isPieceId(state.selectedPieceId)) &&
    (state.selectedDimensionId === null || isFinAttachmentDimensionId(state.selectedDimensionId)) &&
    uniquePieces(state.isolatedPieceIds) &&
    uniquePieces(state.hiddenPieceIds) &&
    state.isolatedPieceIds.every((id) => !state.hiddenPieceIds.includes(id)) &&
    typeof state.partsSidebarOpen === 'boolean' &&
    typeof state.evidenceSidebarOpen === 'boolean' &&
    (state.camera === null || parseFinAttachmentCameraSnapshot(state.camera) !== null)
  );
}

function urlFor(href: string): URL {
  return new URL(href, 'http://local.invalid');
}
function relativeHref(url: URL): string {
  return `${url.pathname}${url.search}${url.hash}`;
}
function piecesFromQuery(value: string | null): FinAttachmentPieceId[] | null {
  if (value === null) return [];
  if (!value) return null;
  const parts = value.split(',');
  return uniquePieces(parts) ? parts : null;
}
function booleanFromQuery(value: string | null): boolean | null {
  if (value === null || value === '1') return true;
  if (value === '0') return false;
  return null;
}

/** Reject duplicated or stale source parameters; never silently open another vehicle. */
export function parseFinAttachmentHref(href: string): FinAttachmentRoute | null {
  const params = urlFor(href).searchParams;
  if (
    [...jointKeys, ...sourceKeys].some((key) => params.getAll(key).length > 1) ||
    [...params.keys()].some(
      (key) => key.startsWith('joint') && !jointKeys.includes(key as never),
    ) ||
    params.get('finJoint') !== '1' ||
    params.get('design') !== RP1_CONNECTIONS_CONFIGURATION ||
    params.get('spec') !== RP1_CONNECTIONS_SHA256 ||
    params.get('jointGeometry') !== FIN_ATTACHMENT_GEOMETRY_REVISION ||
    params.get('jointDetail') !== FIN_ATTACHMENT_DETAIL_REVISION ||
    !isPieceId(params.get('jointOrigin')) ||
    !isSection(params.get('jointSection')) ||
    (params.has('jointPiece') && !isPieceId(params.get('jointPiece'))) ||
    (params.has('jointDimension') && !isFinAttachmentDimensionId(params.get('jointDimension'))) ||
    (params.has('jointDrawing') && !['root', 'loadpath'].includes(params.get('jointDrawing')!)) ||
    (params.get('workspace') !== 'design' && params.get('workspace') !== 'engineering') ||
    (params.has('part') && !RP1_CONNECTION_PART_IDS.some((id) => id === params.get('part'))) ||
    (params.get('workspace') === 'engineering' &&
      (params.get('view') !== 'rp1-connections' || params.get('connection') !== 'fin-root'))
  )
    return null;
  const isolatedPieceIds = piecesFromQuery(params.get('jointIsolate'));
  const hiddenPieceIds = piecesFromQuery(params.get('jointHidden'));
  const partsSidebarOpen = booleanFromQuery(params.get('jointParts'));
  const evidenceSidebarOpen = booleanFromQuery(params.get('jointEvidence'));
  if (
    isolatedPieceIds === null ||
    hiddenPieceIds === null ||
    partsSidebarOpen === null ||
    evidenceSidebarOpen === null
  )
    return null;
  const originPartId = params.get('jointOrigin') as FinAttachmentPieceId;
  if (params.get('workspace') === 'design' && params.get('part') !== originPartId) return null;
  const state: FinAttachmentState = {
    section: params.get('jointSection') as FinAttachmentSection,
    selectedPieceId: (params.get('jointPiece') as FinAttachmentPieceId | null) || null,
    selectedDimensionId: params.get('jointDimension') as FinAttachmentDimensionId | null,
    isolatedPieceIds,
    hiddenPieceIds,
    partsSidebarOpen,
    evidenceSidebarOpen,
    camera: null,
  };
  if (!validFinAttachmentState(state)) return null;
  return {
    state,
    originPartId,
    drawing: (params.get('jointDrawing') as FinAttachmentDrawing | null) || null,
  };
}

function assertCompatibleSource(url: URL): void {
  const params = url.searchParams;
  if (
    [...jointKeys, ...sourceKeys].some((key) => params.getAll(key).length > 1) ||
    (params.has('design') && params.get('design') !== RP1_CONNECTIONS_CONFIGURATION) ||
    (params.has('spec') && params.get('spec') !== RP1_CONNECTIONS_SHA256) ||
    (params.has('jointGeometry') &&
      params.get('jointGeometry') !== FIN_ATTACHMENT_GEOMETRY_REVISION) ||
    (params.has('jointDetail') && params.get('jointDetail') !== FIN_ATTACHMENT_DETAIL_REVISION)
  )
    throw new Error('Fin attachment link unavailable: stale or ambiguous source.');
}

/** Serialize source-bound, shareable inspector state; camera stays in identity-keyed session state. */
export function finAttachmentHref(
  href: string,
  state: FinAttachmentState,
  originPartId: FinAttachmentPieceId,
): string {
  if (!isPieceId(originPartId) || !validFinAttachmentState(state))
    throw new Error('Fin attachment link unavailable: invalid inspection state.');
  const url = urlFor(href);
  assertCompatibleSource(url);
  const params = url.searchParams;
  jointKeys.forEach((key) => params.delete(key));
  params.delete('view');
  params.delete('connection');
  params.delete('cad');
  params.set('workspace', 'design');
  params.set('design', RP1_CONNECTIONS_CONFIGURATION);
  params.set('spec', RP1_CONNECTIONS_SHA256);
  params.set('part', originPartId);
  params.set('finJoint', '1');
  params.set('jointOrigin', originPartId);
  params.set('jointGeometry', FIN_ATTACHMENT_GEOMETRY_REVISION);
  params.set('jointDetail', FIN_ATTACHMENT_DETAIL_REVISION);
  params.set('jointSection', state.section);
  if (state.selectedPieceId) params.set('jointPiece', state.selectedPieceId);
  if (state.selectedDimensionId) params.set('jointDimension', state.selectedDimensionId);
  if (state.isolatedPieceIds.length) params.set('jointIsolate', state.isolatedPieceIds.join(','));
  if (state.hiddenPieceIds.length) params.set('jointHidden', state.hiddenPieceIds.join(','));
  params.set('jointParts', state.partsSidebarOpen ? '1' : '0');
  params.set('jointEvidence', state.evidenceSidebarOpen ? '1' : '0');
  return relativeHref(url);
}

/** Engineering uses the existing RP1 connection view and its two recorded fin drawings. */
export function openFinDrawingHref(
  href: string,
  state: FinAttachmentState,
  originPartId: FinAttachmentPieceId,
  drawing: FinAttachmentDrawing,
): string {
  if (drawing !== 'root' && drawing !== 'loadpath')
    throw new Error('Fin attachment drawing unavailable: unknown drawing.');
  const url = urlFor(finAttachmentHref(href, state, originPartId));
  url.searchParams.set('workspace', 'engineering');
  url.searchParams.set('view', 'rp1-connections');
  url.searchParams.set('connection', 'fin-root');
  url.searchParams.set('part', state.selectedPieceId ?? originPartId);
  url.searchParams.set('jointDrawing', drawing);
  return relativeHref(url);
}

/** Return to the original selected RP1 part even if Engineering selected another part. */
export function returnFinJointHref(href: string): string | null {
  const route = parseFinAttachmentHref(href);
  return route ? finAttachmentHref(href, route.state, route.originPartId) : null;
}

export function finAttachmentSessionKey(originPartId: FinAttachmentPieceId): string {
  if (!isPieceId(originPartId)) throw new Error('Fin attachment camera unavailable: unknown part.');
  return `fin-joint:${RP1_CONNECTIONS_CONFIGURATION}:${RP1_CONNECTIONS_SHA256}:${FIN_ATTACHMENT_GEOMETRY_REVISION}:${originPartId}`;
}

/** Keep the actual scene/controls alive only for the exact joint-to-drawing journey. */
export function retainFinDesignWorkspace(
  workspace: string,
  document: InspectionDocument | null,
  href: string,
): boolean {
  if (workspace === 'design') return true;
  return (
    workspace === 'engineering' &&
    document?.id === RP1_CONNECTIONS_CONFIGURATION &&
    document.identity?.specification_sha256 === RP1_CONNECTIONS_SHA256 &&
    document.identity?.inspection_geometry_sha256 === FIN_ATTACHMENT_GEOMETRY_REVISION &&
    parseFinAttachmentHref(href) !== null
  );
}
