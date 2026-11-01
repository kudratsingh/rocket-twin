/** Ignore completions superseded by a newer request or an explicit cancellation. */
export function requestOrder() {
  let version = 0;
  return {
    begin() {
      const ticket = ++version;
      return () => ticket === version;
    },
    cancel() {
      version += 1;
    },
  };
}
