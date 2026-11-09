import type { MouseEvent, ReactNode } from 'react';
import { workspaceHref, workspaceItems } from './navigation';
import type { WorkspaceId } from './navigation';
import './workspaces.css';
import { WorkspaceLayoutProvider, useWorkspaceLayout } from './workspaceLayoutContext';

export function WorkspaceNavigation({
  active,
  href,
  onNavigate,
}: {
  active: WorkspaceId;
  href: string;
  onNavigate: (workspace: WorkspaceId, href: string) => void;
}) {
  const layout = useWorkspaceLayout();
  const icons: Record<WorkspaceId, string> = {
    design: '◇',
    engineering: '⌘',
    experiments: '⚗',
    replay: '▷',
    analysis: '▥',
  };
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
            aria-label={layout ? item.label : undefined}
            title={layout ? item.label : undefined}
            onClick={(event) => navigate(event, item.id, next)}
          >
            {layout ? (
              <>
                <span className="revamp-workspace-icon" aria-hidden="true">
                  {icons[item.id]}
                </span>
                <span className="revamp-visually-hidden">{item.label}</span>
              </>
            ) : (
              item.label
            )}
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
  workspace,
  retainDesign = false,
}: {
  header: ReactNode;
  navigation: ReactNode;
  identity: ReactNode;
  children: ReactNode;
  footer?: ReactNode;
  workspace?: WorkspaceId;
  retainDesign?: boolean;
}) {
  if (workspace === 'design' || retainDesign)
    return (
      <WorkspaceLayoutProvider workspace="design" source={identity}>
        <DesignWorkspaceFrame
          header={header}
          navigation={navigation}
          footer={footer}
          active={workspace === 'design'}
        >
          {children}
        </DesignWorkspaceFrame>
      </WorkspaceLayoutProvider>
    );
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

function DesignWorkspaceFrame({
  active = true,
  header,
  navigation,
  children,
  footer,
}: {
  active?: boolean;
  header: ReactNode;
  navigation: ReactNode;
  children: ReactNode;
  footer?: ReactNode;
}) {
  const layout = useWorkspaceLayout()!;
  const { preferences, id } = layout;
  return (
    <div
      className="research-shell revamp-design revamp-design-shell"
      data-focused={layout.focused}
      data-rail={preferences.railOpen}
    >
      <a className="research-skip-link" href="#workspace-content">
        Skip to workspace
      </a>
      <div className="revamp-header">
        <div
          className="revamp-layout-controls revamp-panel-controls"
          role="group"
          aria-label="Design panels"
          hidden={!active}
        >
          <button
            type="button"
            id={`${id}-rail-toggle`}
            className="revamp-panel-toggle revamp-navigation-toggle"
            aria-controls={`${id}-rail`}
            aria-expanded={preferences.railOpen}
            onClick={layout.toggleRail}
          >
            {preferences.railOpen ? 'Hide navigation' : 'Show navigation'}
          </button>
          <button
            type="button"
            id={`${id}-context-toggle`}
            className="revamp-panel-toggle revamp-sidebar-toggle"
            aria-controls={`${id}-context`}
            aria-expanded={preferences.contextOpen}
            onClick={layout.toggleContext}
          >
            {preferences.contextOpen ? 'Hide parts sidebar' : 'Show parts sidebar'}
          </button>
        </div>
        <div className="revamp-header-main">{header}</div>
        <div className="revamp-layout-controls" aria-label="Design layout" hidden={!active}>
          <button
            type="button"
            id={`${id}-focus`}
            className="revamp-focus-toggle"
            aria-pressed={layout.focused}
            onClick={layout.toggleFocus}
          >
            {layout.focused ? 'Exit focus' : 'Focus'}
          </button>
          <details
            className="revamp-layout-menu"
            onKeyDown={(event) => {
              if (event.key === 'Escape' && !event.defaultPrevented) {
                event.preventDefault();
                event.stopPropagation();
                event.currentTarget.open = false;
                event.currentTarget.querySelector('summary')?.focus();
              }
            }}
          >
            <summary aria-label="Layout menu" title="Layout menu">
              Layout
            </summary>
            <div>
              <button type="button" onClick={layout.resetLayout}>
                Reset layout
              </button>
              <button type="button" onClick={layout.toggleTools}>
                {preferences.toolsOpen ? 'Close scene tools' : 'Open scene tools'}
              </button>
              <p>
                Focus hides both sidebars and closes tools. Escape restores your previous layout.
                Use / to find a component.
              </p>
            </div>
          </details>
        </div>
      </div>
      <div className="revamp-design-body">
        <div className="revamp-workspace-rail" id={`${id}-rail`} hidden={!preferences.railOpen}>
          {navigation}
        </div>
        <div
          className="research-scroll-region revamp-design-content"
          id="workspace-content"
          tabIndex={-1}
          style={active ? undefined : { overflow: 'auto', display: 'block' }}
        >
          {children}
        </div>
      </div>
      {footer && <div className="revamp-footer">{footer}</div>}
    </div>
  );
}
