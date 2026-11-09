import { jumpToReplaySection, replaySections } from './replaySectionTarget.ts';
import './replaySectionNavigation.css';

/** Normal-flow sticky shortcuts; no new replay state, hooks or scene instance. */
export function ReplaySectionNavigation() {
  return (
    <nav className="replay-section-navigation" aria-label="Replay sections">
      {replaySections.map(([section, label]) => (
        <button
          key={section}
          type="button"
          onClick={(event) => jumpToReplaySection(event.currentTarget, section)}
        >
          {label}
        </button>
      ))}
    </nav>
  );
}
