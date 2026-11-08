import { Component } from 'react';
import type { ReactNode } from 'react';

export function workspaceRecoveryHref(href: string): string {
  const url = new URL(href, 'http://rocket-twin.local');
  url.searchParams.delete('__previewFault');
  return `${url.pathname}${url.search}${url.hash}`;
}

/** Explicit software fixture only: never enabled by a production build. */
export function workspaceRenderFailureRequested(dev: boolean, href: string, workspace: string) {
  return (
    dev &&
    new URL(href, 'http://rocket-twin.local').searchParams.get('__previewFault') ===
      `${workspace}-render`
  );
}

export function WorkspaceRenderFailureFixture(): never {
  throw new Error('Intentional development-only rendering fixture; no calculation was executed.');
}

/** Keep navigation outside a failed lazy/rendering subtree; no saved data is modified. */
export class WorkspaceFailureBoundary extends Component<
  { workspace: string; children: ReactNode },
  { error: string | null }
> {
  state: { error: string | null } = { error: null };

  static getDerivedStateFromError(error: unknown) {
    return {
      error: error instanceof Error ? error.message : 'Unexpected workspace display error.',
    };
  }

  render() {
    if (!this.state.error) return this.props.children;
    const href = workspaceRecoveryHref(typeof window === 'undefined' ? '/' : window.location.href);
    return (
      <main className="center-state" role="alert">
        <h1>This workspace could not be displayed</h1>
        <p>
          The {this.props.workspace} view encountered a display or module-loading error. Saved
          designs and experiment records have not been changed. Use the workspace navigation to
          continue elsewhere, or reload this view after the cause is corrected.
        </p>
        <p>{this.state.error}</p>
        <a className="primary-button" href={href}>
          Reload this workspace
        </a>
      </main>
    );
  }
}
