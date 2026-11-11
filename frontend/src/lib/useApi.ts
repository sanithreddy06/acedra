import { useCallback, useEffect, useRef, useState } from 'react';
import { api, errorMessage, type Params } from './api';

export interface ApiState<T> {
  data: T | null;
  error: string | null;
  loading: boolean;
  reload: () => Promise<void>;
  setData: (data: T | null) => void;
}

/**
 * Fetch a GET endpoint with loading / error / reload. Pass `null` as the path to skip the request.
 * Responses that arrive after a newer request (or after the path changed) are ignored.
 */
export function useApi<T>(path: string | null, params?: Params): ApiState<T> {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(!!path);
  const key = path ? path + JSON.stringify(params || {}) : null;
  const seq = useRef(0);

  const load = useCallback(async () => {
    if (!path) { setLoading(false); return; }
    const id = ++seq.current;
    setLoading(true); setError(null);
    try {
      const d = await api.get<T>(path, params);
      if (id === seq.current) setData(d);
    } catch (e) {
      if (id === seq.current) setError(errorMessage(e, 'Could not load this information.'));
    } finally {
      if (id === seq.current) setLoading(false);
    }
    // `key` captures path and params; listing them separately would refetch on every render.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);

  useEffect(() => { load(); }, [load]);
  return { data, error, loading, reload: load, setData };
}
