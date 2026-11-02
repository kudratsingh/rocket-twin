/** Search only recorded identifiers and displayed part attributes. */
export function matchesPartSearch(
  query: string,
  part: { id: string; name: string; type: string; material: string },
): boolean {
  const term = query.trim().toLowerCase();
  return `${part.name} ${part.type} ${part.material} ${part.id}`.toLowerCase().includes(term);
}
