/** Experiment context is independent of the active engineering design. */
export function experimentConfiguration(search: string, design: string) {
  return new URLSearchParams(search).get('experiment') || design;
}
export function experimentHref(href: string, configuration: string) {
  const url = new URL(href, 'http://local.invalid');
  if (url.searchParams.get('experiment') !== configuration) {
    url.searchParams.delete('run');
    url.searchParams.delete('compare');
  }
  url.searchParams.set('experiment', configuration);
  return `${url.pathname}${url.search}${url.hash}`;
}
export function savedRunHref(href: string, id: string | null, comparison: boolean) {
  const url = new URL(href, 'http://local.invalid');
  const key = comparison ? 'compare' : 'run';
  if (id === null) url.searchParams.delete(key);
  else url.searchParams.set(key, id);
  return `${url.pathname}${url.search}${url.hash}`;
}
