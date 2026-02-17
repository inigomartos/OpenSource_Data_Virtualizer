import useSWR, { mutate as globalMutate } from 'swr';
import { apiClient } from '@/lib/api-client';
import { ListResponse } from '@/types/common';
import type {
  Dashboard,
  DashboardWithWidgets,
  CreateDashboardPayload,
  UpdateDashboardPayload,
  CreateWidgetPayload,
  UpdateWidgetPayload,
  WidgetWithData,
} from '@/types/dashboard';

export function useDashboards() {
  const { data, error, mutate } = useSWR<ListResponse<Dashboard>>(
    '/dashboards',
    apiClient
  );

  return {
    dashboards: data?.data || [],
    isLoading: !error && !data,
    error,
    refresh: mutate,
  };
}

export function useDashboard(id: string | null) {
  const { data, error, mutate } = useSWR<DashboardWithWidgets>(
    id ? `/dashboards/${id}` : null,
    apiClient
  );

  return {
    dashboard: data || null,
    isLoading: !error && !data,
    error,
    refresh: mutate,
  };
}

export async function createDashboard(
  payload: CreateDashboardPayload
): Promise<Dashboard> {
  const result = await apiClient<Dashboard>('/dashboards', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  await globalMutate('/dashboards');
  return result;
}

export async function updateDashboard(
  id: string,
  payload: UpdateDashboardPayload
): Promise<Dashboard> {
  const result = await apiClient<Dashboard>(`/dashboards/${id}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  });
  await globalMutate('/dashboards');
  await globalMutate(`/dashboards/${id}`);
  return result;
}

export async function deleteDashboard(id: string): Promise<void> {
  await apiClient(`/dashboards/${id}`, { method: 'DELETE' });
  await globalMutate('/dashboards');
}

export async function addWidget(
  dashboardId: string,
  payload: CreateWidgetPayload
): Promise<WidgetWithData> {
  const result = await apiClient<WidgetWithData>(
    `/dashboards/${dashboardId}/widgets`,
    {
      method: 'POST',
      body: JSON.stringify(payload),
    }
  );
  await globalMutate(`/dashboards/${dashboardId}`);
  return result;
}

export async function updateWidget(
  dashboardId: string,
  widgetId: string,
  payload: UpdateWidgetPayload
): Promise<WidgetWithData> {
  const result = await apiClient<WidgetWithData>(
    `/dashboards/${dashboardId}/widgets/${widgetId}`,
    {
      method: 'PUT',
      body: JSON.stringify(payload),
    }
  );
  await globalMutate(`/dashboards/${dashboardId}`);
  return result;
}

export async function deleteWidget(
  dashboardId: string,
  widgetId: string
): Promise<void> {
  await apiClient(`/dashboards/${dashboardId}/widgets/${widgetId}`, {
    method: 'DELETE',
  });
  await globalMutate(`/dashboards/${dashboardId}`);
}

export async function refreshWidget(
  dashboardId: string,
  widgetId: string
): Promise<WidgetWithData> {
  const result = await apiClient<WidgetWithData>(
    `/dashboards/${dashboardId}/widgets/${widgetId}/refresh`,
    {
      method: 'POST',
    }
  );
  await globalMutate(`/dashboards/${dashboardId}`);
  return result;
}
