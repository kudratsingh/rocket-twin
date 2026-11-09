/** Ordinary same-origin DEV fixture. It never drives or inspects app controls. */
export const VIEWPORT_PRESETS = [
  { width: 1440, height: 900 },
  { width: 1280, height: 720 },
  { width: 900, height: 720 },
] as const;
export type ViewportPreset = (typeof VIEWPORT_PRESETS)[number];

const APP_PATH =
  '/?workspace=design&design=G80-F2-RP1-AD1-definition-v2&spec=811b3bed631fe2ce30a6b0211beecb739d40ebbbcb10e063f6beba0854631660';

export function allowedFixtureUrl(href: string, dev: boolean): boolean {
  if (!dev) return false;
  try {
    const url = new URL(href);
    return (
      url.protocol === 'http:' &&
      (url.hostname === '127.0.0.1' || url.hostname === 'localhost' || url.hostname === '[::1]') &&
      url.port === '5173' &&
      url.pathname === '/viewport-check.html' &&
      url.search === '' &&
      url.hash === '' &&
      url.username === '' &&
      url.password === ''
    );
  } catch {
    return false;
  }
}

export function fixedAppUrl(fixtureHref: string, dev: boolean): string | null {
  if (!allowedFixtureUrl(fixtureHref, dev)) return null;
  return new URL(APP_PATH, new URL(fixtureHref).origin).href;
}

export function presetFor(width: number, height: number): ViewportPreset | null {
  return (
    VIEWPORT_PRESETS.find((preset) => preset.width === width && preset.height === height) ?? null
  );
}

/** A preset changes only the existing iframe's CSS box; it never changes its src. */
export function applyPreset(frame: Pick<HTMLIFrameElement, 'style'>, preset: ViewportPreset): void {
  if (!presetFor(preset.width, preset.height)) throw new Error('Unsupported viewport preset');
  frame.style.width = `${preset.width}px`;
  frame.style.height = `${preset.height}px`;
}

type FrameRead = Pick<
  HTMLIFrameElement,
  'contentWindow' | 'contentDocument' | 'getBoundingClientRect'
>;
type ObservedViewport = {
  requested: ViewportPreset;
  inner_width: number | null;
  inner_height: number | null;
  device_pixel_ratio: number | null;
  document_client_width: number | null;
  document_client_height: number | null;
  frame_rect_width: number | null;
  frame_rect_height: number | null;
  requested_matches_actual: boolean | null;
};

function positive(value: unknown): number | null {
  return typeof value === 'number' && Number.isFinite(value) && value > 0 ? value : null;
}

export function readActualViewport(
  frame: FrameRead,
  preset: ViewportPreset,
  loaded: boolean,
): ObservedViewport {
  const unknown: ObservedViewport = {
    requested: preset,
    inner_width: null,
    inner_height: null,
    device_pixel_ratio: null,
    document_client_width: null,
    document_client_height: null,
    frame_rect_width: null,
    frame_rect_height: null,
    requested_matches_actual: null,
  };
  if (!loaded) return unknown;
  try {
    const child = frame.contentWindow;
    const doc = frame.contentDocument;
    if (!child || !doc?.documentElement) return unknown;
    const rect = frame.getBoundingClientRect();
    const observed = {
      ...unknown,
      inner_width: positive(child.innerWidth),
      inner_height: positive(child.innerHeight),
      device_pixel_ratio: positive(child.devicePixelRatio),
      document_client_width: positive(doc.documentElement.clientWidth),
      document_client_height: positive(doc.documentElement.clientHeight),
      frame_rect_width: positive(rect.width),
      frame_rect_height: positive(rect.height),
    };
    observed.requested_matches_actual =
      observed.inner_width === null ||
      observed.inner_height === null ||
      observed.device_pixel_ratio === null ||
      observed.document_client_width === null ||
      observed.document_client_height === null ||
      observed.frame_rect_width === null ||
      observed.frame_rect_height === null
        ? null
        : observed.inner_width === preset.width &&
          observed.inner_height === preset.height &&
          observed.frame_rect_width === preset.width &&
          observed.frame_rect_height === preset.height;
    return observed;
  } catch {
    return unknown;
  }
}

function boot(): void {
  const root = document.getElementById('fixture-root');
  const controls = document.getElementById('preset-controls');
  const measurements = document.getElementById('measurements');
  if (!root || !controls || !measurements) return;
  const appUrl = fixedAppUrl(window.location.href, import.meta.env.DEV);
  if (!appUrl) {
    root.className = 'blocked';
    root.textContent = 'Unavailable: this fixed fixture requires the loopback DEV page.';
    measurements.textContent = 'Actual viewport unavailable.';
    return;
  }
  const frame = document.createElement('iframe');
  frame.title = 'Actual Rocket Twin app at requested embedded CSS viewport';
  frame.src = appUrl;
  frame.setAttribute('referrerpolicy', 'same-origin');
  let preset: ViewportPreset = VIEWPORT_PRESETS[0];
  let loaded = false;
  const buttons: HTMLButtonElement[] = [];
  const refresh = () => {
    const actual = readActualViewport(frame, preset, loaded);
    const value = (number: number | null) => (number === null ? 'unavailable' : String(number));
    measurements.textContent =
      `Requested ${preset.width}×${preset.height} CSS; ` +
      `actual inner ${value(actual.inner_width)}×${value(actual.inner_height)}, ` +
      `document client ${value(actual.document_client_width)}×${value(actual.document_client_height)}, ` +
      `frame rect ${value(actual.frame_rect_width)}×${value(actual.frame_rect_height)}, ` +
      `DPR ${value(actual.device_pixel_ratio)}; ` +
      `size match ${actual.requested_matches_actual === null ? 'unavailable' : actual.requested_matches_actual ? 'yes' : 'no'}. ` +
      'Outer browser viewport unchanged. Embedded measurements alone do not establish acceptance.';
  };
  const select = (next: ViewportPreset) => {
    preset = next;
    applyPreset(frame, next);
    buttons.forEach((button) => {
      button.setAttribute(
        'aria-pressed',
        String(button.dataset.size === `${next.width}×${next.height}`),
      );
    });
    window.requestAnimationFrame(refresh);
  };
  for (const option of VIEWPORT_PRESETS) {
    const button = document.createElement('button');
    button.type = 'button';
    button.dataset.size = `${option.width}×${option.height}`;
    button.textContent = button.dataset.size;
    button.addEventListener('click', () => select(option));
    buttons.push(button);
    controls.append(button);
  }
  frame.addEventListener('load', () => {
    loaded = true;
    refresh();
  });
  applyPreset(frame, preset);
  root.append(frame);
  select(preset);
  window.addEventListener('resize', refresh);
}

if (typeof document !== 'undefined') boot();
