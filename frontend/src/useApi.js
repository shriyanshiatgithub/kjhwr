import { useEffect, useState } from "react";

/**
 * Run an async loader whenever `deps` change.
 * Returns { data, error, loading }. Cancels the in-flight request on change/unmount
 * so a slow old response can never overwrite a newer one.
 */
export function useApi(loader, deps) {
  const [state, setState] = useState({ data: null, error: null, loading: true });

  useEffect(() => {
    const controller = new AbortController();
    setState((s) => ({ ...s, loading: true, error: null }));
    loader(controller.signal)
      .then((data) => setState({ data, error: null, loading: false }))
      .catch((error) => {
        if (error.name === "AbortError") return;
        setState({ data: null, error: error.message, loading: false });
      });
    return () => controller.abort();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return state;
}
