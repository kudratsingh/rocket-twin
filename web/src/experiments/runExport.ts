import { comparisonDifferences } from './comparison.ts';

/** Export the returned playback samples and their provenance without resampling. */
export type ExportRun = {
  record: { run_id: string; [key: string]: unknown };
  telemetry: {
    columns: Record<string, (number | null)[]>;
    [key: string]: unknown;
  };
};

export type ExportSelection = {
  start_s: number;
  end_s: number;
  offset_s: number;
  alignment_event: string | null;
  peer_offset_s?: number;
};

function selectedIndices(times: (number | null)[], selection?: ExportSelection): number[] {
  if (
    selection &&
    (!Number.isFinite(selection.start_s) ||
      !Number.isFinite(selection.end_s) ||
      !Number.isFinite(selection.offset_s) ||
      selection.end_s < selection.start_s)
  )
    throw new Error('Export selection has an invalid range or clock offset.');
  return times.flatMap((time, index) =>
    typeof time === 'number' &&
    (!selection ||
      (time - selection.offset_s >= selection.start_s &&
        time - selection.offset_s <= selection.end_s))
      ? [index]
      : [],
  );
}

function csvCell(value: string): string {
  return /[",\r\n]/.test(value) ? `"${value.replace(/"/g, '""')}"` : value;
}

/** CSV and its companion metadata must agree on whether recorded coverage exists. */
function exportColumns(run: ExportRun) {
  const columns = run.telemetry.columns;
  const times = columns.time_s;
  if (
    !Array.isArray(times) ||
    !times.length ||
    !times.every(
      (time, index) =>
        typeof time === 'number' &&
        Number.isFinite(time) &&
        (index === 0 || time > (times[index - 1] as number)),
    )
  )
    throw new Error('Playback time samples are missing, nonfinite or not strictly increasing.');
  const names = [
    'time_s',
    ...Object.keys(columns)
      .filter((name) => name !== 'time_s')
      .sort(),
  ];
  for (const name of names) {
    if (!Array.isArray(columns[name]) || columns[name].length > times.length)
      throw new Error(`Channel ${name} has invalid coverage; export is withheld.`);
  }
  return { columns, times, names };
}

export function telemetryCsv(run: ExportRun, selection?: ExportSelection): string {
  const { columns, times, names } = exportColumns(run);
  const rows = [names.map(csvCell).join(',')];
  for (const i of selectedIndices(times, selection)) {
    rows.push(
      names
        .map((name) => {
          const value = columns[name][i];
          return typeof value === 'number' && Number.isFinite(value) ? String(value) : '';
        })
        .join(','),
    );
  }
  return `${rows.join('\r\n')}\r\n`;
}

export function exportMetadata(
  run: ExportRun,
  other?: ExportRun | null,
  selection?: ExportSelection,
): string {
  const { times } = exportColumns(run);
  if (other) exportColumns(other);
  const { columns, ...telemetryInfo } = run.telemetry;
  const native =
    (run.telemetry.sampling as { mode?: string } | undefined)?.mode === 'full-rate-benchmark';
  const info = {
    format: native
      ? 'rocket-twin-native-playback-export-v1'
      : 'rocket-twin-decimated-playback-export-v1',
    scope: native
      ? 'Native-rate returned samples with backend-derived display channels; selection may restrict coverage. No interpolation or extrapolation; not flight evidence.'
      : 'Returned playback samples; some channels are backend-derived. No interpolation or extrapolation; not full-resolution telemetry or flight evidence.',
    selected_run: run.record,
    selection: selection
      ? {
          ...selection,
          clock: 'display_s = recorded_time_s - offset_s; CSV keeps original recorded time_s',
          selected_sample_count: selectedIndices(times, selection).length,
          range_policy: 'inclusive recorded samples only; no synthetic boundary samples',
        }
      : null,
    playback: telemetryInfo,
    coverage: {
      returned_sample_count: Array.isArray(times) ? times.length : null,
      first_time_s: times?.[0] ?? null,
      last_time_s: times?.at(-1) ?? null,
      channel_sample_counts: Object.fromEntries(
        Object.entries(columns).map(([key, values]) => [
          key,
          Array.isArray(values) ? values.length : null,
        ]),
      ),
    },
    comparison_differences: other
      ? comparisonDifferences(
          run.record as Parameters<typeof comparisonDifferences>[0],
          other.record as Parameters<typeof comparisonDifferences>[1],
        )
      : null,
    comparison_run: other
      ? {
          record: other.record,
          playback: Object.fromEntries(
            Object.entries(other.telemetry).filter(([key]) => key !== 'columns'),
          ),
          coverage: {
            returned_sample_count: other.telemetry.columns.time_s?.length ?? null,
            first_time_s: other.telemetry.columns.time_s?.[0] ?? null,
            last_time_s: other.telemetry.columns.time_s?.at(-1) ?? null,
            selected_sample_count: selection
              ? selectedIndices(other.telemetry.columns.time_s, {
                  ...selection,
                  offset_s: selection.peer_offset_s ?? 0,
                }).length
              : null,
          },
        }
      : null,
  };
  return `${JSON.stringify(info, null, 2)}\n`;
}

export type DraftResult =
  { ok: true; wind: number; direction: number; gust: number } | { ok: false; reason: string };

/** Only copy a complete representable request into the current form; never switch the active design. */
export function recordedSettingsDraft(
  record: Record<string, unknown>,
  active: string,
): DraftResult {
  const settings = record.settings;
  if (!settings || typeof settings !== 'object' || Array.isArray(settings))
    return { ok: false, reason: 'Recorded request settings are unavailable.' };
  const s = settings as Record<string, unknown>;
  const allowed = ['configuration', 'wind_mps', 'wind_direction_deg', 'gust_mps', 'preset'];
  if (Object.keys(s).some((key) => !allowed.includes(key)))
    return {
      ok: false,
      reason: 'The recorded request contains fields this form cannot represent.',
    };
  if (
    record.configuration !== active ||
    record.vehicle_id !== active ||
    s.configuration !== active ||
    ![
      'modular-performance-v1',
      'modular-performance-g54-hypothesis',
      'modular-tvc-finned-v1',
    ].includes(active)
  )
    return {
      ok: false,
      reason: 'Select the same supported complete configuration before reusing settings.',
    };
  if (s.preset !== 'sim' || record.controller !== 'locked, unguided')
    return {
      ok: false,
      reason: 'The recorded preset or controller is incompatible with this form.',
    };
  const { wind_mps: wind, wind_direction_deg: direction, gust_mps: gust } = s;
  if (
    typeof wind !== 'number' ||
    !Number.isFinite(wind) ||
    wind < 0 ||
    wind > 10 ||
    typeof direction !== 'number' ||
    !Number.isFinite(direction) ||
    direction < 0 ||
    direction >= 360 ||
    typeof gust !== 'number' ||
    !Number.isFinite(gust) ||
    gust < 0 ||
    gust > 5
  )
    return { ok: false, reason: 'Recorded wind settings are missing or outside supported ranges.' };
  return { ok: true, wind, direction, gust };
}
