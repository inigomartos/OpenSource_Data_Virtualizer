import useSWR from 'swr';
import { apiClient } from '@/lib/api-client';
import type { Dashboard } from '@/types/dashboard';

export function useDashboards() {
  const { data, error, mutate } = useSWR<{ dashboards: Dashboard[] }>(
    '/dashboards',
    apiClient
  );

  return {
    dashboards: data?.dashboards || [],
    isLoading: !error && !data,
    error,
    refresh: mutate,
  };
}
