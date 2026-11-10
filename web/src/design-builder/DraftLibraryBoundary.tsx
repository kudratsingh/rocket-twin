import { Component } from 'react';
import type { ReactNode } from 'react';

type Props = { children: ReactNode; onReturnToSource: () => void };
type State = { diagnostic: string | null };

/** A failed optional draft panel must not unmount the frozen rocket or its controls. */
export class DraftLibraryBoundary extends Component<Props, State> {
  state: State = { diagnostic: null };

  static getDerivedStateFromError(error: unknown): State {
    return {
      diagnostic: error instanceof Error ? error.message.slice(0, 500) : 'Unknown client exception',
    };
  }

  render() {
    if (this.state.diagnostic !== null)
      return (
        <section className="draft-library" aria-label="Draft library unavailable">
          <h3>Draft library could not load</h3>
          <p role="alert">
            This optional panel failed. The frozen rocket remains available. No draft save is
            confirmed; no automatic retry or replacement data was used.
          </p>
          <details>
            <summary>Client diagnostic</summary>
            <p>{this.state.diagnostic || 'The client supplied no diagnostic text.'}</p>
          </details>
          <button type="button" onClick={this.props.onReturnToSource}>
            Return to frozen rocket
          </button>
        </section>
      );
    return this.props.children;
  }
}
