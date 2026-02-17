import useSWR from 'swr';
import { apiClient } from '@/lib/api-client';

export function useSchema(connectionId: string | null) {
  const { data, error, mutate } = useSWR(
    connectionId ? `/schema/${connectionId}` : null,
    apiClient
  );

  return {
    schema: data?.tables || [],
    isLoading: !error && !data,
    error,
    refresh: mutate,
  };
}
