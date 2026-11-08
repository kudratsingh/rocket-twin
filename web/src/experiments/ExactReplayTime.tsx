import { useId, useState } from 'react';
import { exactReplayTime } from './replayTimeValue';

/** Separate draft avoids interrupting typing when the playback clock advances. */
export function ExactReplayTime({
  time,
  start,
  end,
  aligned,
  onApply,
}: {
  time: number;
  start: number;
  end: number;
  aligned: boolean;
  onApply: (time: number) => void;
}) {
  const id = useId();
  const [draft, setDraft] = useState<string | null>(null);
  const [error, setError] = useState('');
  return (
    <form
      noValidate
      style={{ display: 'flex', gap: 6, alignItems: 'end', flexWrap: 'wrap' }}
      onSubmit={(event) => {
        event.preventDefault();
        const result = exactReplayTime(draft ?? String(time), start, end);
        if (!result.ok) {
          setError(result.reason);
          return;
        }
        onApply(result.time);
        setDraft(null);
        setError('');
      }}
    >
      <label htmlFor={id}>
        Exact replay time (seconds{aligned ? ', aligned clock' : ', elapsed clock'})
        <input
          id={id}
          type="number"
          inputMode="decimal"
          step="any"
          value={draft ?? String(time)}
          style={{ width: '9rem', minWidth: '7rem' }}
          aria-invalid={!!error}
          aria-describedby={`${id}-message`}
          onChange={(event) => {
            setDraft(event.target.value);
            setError('');
          }}
          onKeyDown={(event) => {
            if (event.key === 'Escape') {
              event.preventDefault();
              setDraft(null);
              setError('');
            }
          }}
        />
      </label>
      <button type="submit">Go to exact time</button>
      <span id={`${id}-message`} role={error ? 'alert' : 'status'} style={{ flexBasis: '100%' }}>
        {error ||
          `Enter/Go pauses at the exact value; window ${start.toFixed(3)}–${end.toFixed(3)} s. Escape resets the draft.`}
      </span>
    </form>
  );
}
