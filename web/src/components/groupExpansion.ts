/** A new pick reveals its group; a manual collapse remains effective until the next pick. */
export function functionalGroupOpen(
  groupId: string,
  searching: boolean,
  activeGroupId: string | null,
  selectionToken: number,
  collapsedAt: Record<string, number | undefined>,
): boolean {
  const closed = collapsedAt[groupId];
  return (
    searching || closed === undefined || (activeGroupId === groupId && closed !== selectionToken)
  );
}
