import type { MouseEvent, ReactNode } from 'react';
import { workspaceHref, workspaceItems } from './navigation';
import type { WorkspaceId } from './navigation';
import './workspaces.css';

export function WorkspaceNavigation({
  active,
  href,
  onNavigate,
}: {
  active: WorkspaceId;
  href: string;
  onNavigate: (workspace: WorkspaceId, href: string) => void;
}) {
  function navigate(event: MouseEvent<HTMLAnchorElement>, workspace: WorkspaceId, next: string) {
    if (event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey)
      return;
    event.preventDefault();
    onNavigate(workspace, next);
  }
  return (
    <nav className="research-navigation" aria-label="Research workspaces">
      {workspaceItems.map((item) => {
        const next = workspaceHref(href, item.id);
        return (
          <a
            key={item.id}
            href={next}
            aria-current={active === item.id ? 'page' : undefined}
            onClick={(event) => navigate(event, item.id, next)}
          >
            {item.label}
          </a>
        );
      })}
    </nav>
  );
}

/** Text is supplied from the displayed resource, never inferred from a workspace name. */
export function WorkspaceIdentityStrip({
  name,
  maturity,
  status = 'Engineering acceptance open',
  resource,
  state = 'ready',
  details,
}: {
  name: string;
  maturity: string;
  status?: string;
  resource?: string;
  state?: 'ready' | 'loading' | 'unavailable';
  details?: ReactNode;
}) {
  return (
    <section className="research-identity" aria-label="Displayed source and status">
      <div className="research-identity-summary">
        <strong>{name}</strong>
        <span>{maturity}</span>
        {resource && <span>{resource}</span>}
        {state !== 'ready' && (
          <span role="status">{state === 'loading' ? 'Loading source' : 'Source unavailable'}</span>
        )}
        <span className="research-open-status">{status}</span>
      </div>
      {details && (
        <details className="research-source-details">
          <summary>Source & limitations</summary>
          <div>{details}</div>
        </details>
      )}
    </section>
  );
}

/** The content region owns scrolling; header/navigation stay reachable. */
export function WorkspaceFrame({
  header,
  navigation,
  identity,
  children,
  footer,
}: {
  header: ReactNode;
  navigation: ReactNode;
  identity: ReactNode;
  children: ReactNode;
  footer?: ReactNode;
}) {
  return (
    <div className="research-shell">
      <a className="research-skip-link" href="#workspace-content">
        Skip to workspace
      </a>
      {header}
      {navigation}
      <div className="research-scroll-region" id="workspace-content" tabIndex={-1}>
        {identity}
        {children}
      </div>
      {footer}
    </div>
  );
}
