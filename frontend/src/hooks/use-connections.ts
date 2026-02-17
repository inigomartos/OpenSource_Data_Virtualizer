import useSWR from 'swr';
import { apiClient } from '@/lib/api-client';
import type { Connection } from '@/types/connection';

export function useConnections() {
  const { data, error, mutate } = useSWR<{ connections: Connection[] }>(
    '/connections',
    apiClient
  );

  return {
    connections: data?.connections || [],
    isLoading: !error && !data,
    error,
    refresh: mutate,
  };
}
