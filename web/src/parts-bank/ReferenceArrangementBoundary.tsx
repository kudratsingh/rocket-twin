import { Component } from 'react';
import type { ReactNode } from 'react';

/** Contain optional lazy/DOM failures without taking down installed inspection. */
export class ReferenceArrangementBoundary extends Component<
  { children: ReactNode; onReturn: () => void },
  { failed: boolean }
> {
  state = { failed: false };
  static getDerivedStateFromError() {
    return { failed: true };
  }
  render() {
    return this.state.failed ? (
      <section role="alert">
        <h3>Local reference arrangement unavailable</h3>
        <p>
          The optional arrangement could not open. The source rocket and saved drafts are unchanged.
        </p>
        <button type="button" onClick={this.props.onReturn}>
          Return to rocket
        </button>
      </section>
    ) : (
      this.props.children
    );
  }
}
