const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

interface FetchOptions extends RequestInit {
  skipAuth?: boolean;
}

// Mutex to prevent concurrent refresh attempts
let refreshPromise: Promise<boolean> | null = null;

async function attemptTokenRefresh(): Promise<boolean> {
  try {
    const res = await fetch(`${API_URL}/auth/refresh`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
    });
    return res.ok;
  } catch {
    return false;
  }
}

async function refreshTokenOnce(): Promise<boolean> {
  if (refreshPromise) {
    return refreshPromise;
  }
  refreshPromise = attemptTokenRefresh();
  try {
    return await refreshPromise;
  } finally {
    refreshPromise = null;
  }
}

export async function apiClient<T = any>(
  endpoint: string,
  options: FetchOptions = {}
): Promise<T> {
  const { skipAuth = false, headers: customHeaders, ...rest } = options;

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...((customHeaders as Record<string, string>) || {}),
  };

  const res = await fetch(`${API_URL}${endpoint}`, {
    headers,
    credentials: 'include',
    ...rest,
  });

  if (res.status === 401 && !skipAuth) {
    // Attempt silent token refresh
    const refreshed = await refreshTokenOnce();

    if (refreshed) {
      // Retry the original request with new cookies
      const retryRes = await fetch(`${API_URL}${endpoint}`, {
        headers,
        credentials: 'include',
        ...rest,
      });

      if (retryRes.status === 401) {
        if (typeof window !== 'undefined') {
          window.location.href = '/login';
        }
        throw new Error('Unauthorized');
      }

      if (!retryRes.ok) {
        const error = await retryRes.json().catch(() => ({ detail: 'Request failed' }));
        throw new Error(error.detail || `HTTP ${retryRes.status}`);
      }

      if (retryRes.status === 204) return undefined as T;
      return retryRes.json();
    }

    // Refresh failed — redirect to login
    if (typeof window !== 'undefined') {
      window.location.href = '/login';
    }
    throw new Error('Unauthorized');
  }

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(error.detail || `HTTP ${res.status}`);
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}
