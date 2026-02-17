import useSWR from 'swr';
import { apiClient } from '@/lib/api-client';
import { ListResponse } from '@/types/common';
import type { Connection } from '@/types/connection';

export function useConnections() {
  const { data, error, mutate } = useSWR<ListResponse<Connection>>(
    '/connections',
    apiClient
  );

  return {
    connections: data?.data || [],
    isLoading: !error && !data,
    error,
    refresh: mutate,
  };
}
