import apiClient from './client'

export interface GroupingRunStartResponse {
  run_id: string
}

export interface GroupingStatusResponse {
  stage: string
  current: number
  total: number
  status: string
  groups_found?: number
  error?: string
}

export interface GroupingRunRead {
  id: string
  status: string
  threshold: number
  context: string
  started_at: string
  finished_at: string | null
  projects_processed: number | null
  groups_found: number | null
  projects_in_groups: number | null
  error_message: string | null
  confirmed_rate: number | null
}

export interface GroupingHistoryResponse {
  items: GroupingRunRead[]
  total: number
}

export const groupingApi = {
  async startGrouping(threshold: number, context: string): Promise<GroupingRunStartResponse> {
    const { data } = await apiClient.post<GroupingRunStartResponse>('/grouping/run', {
      threshold,
      context,
    })
    return data
  },

  async getGroupingStatus(runId: string): Promise<GroupingStatusResponse> {
    const { data } = await apiClient.get<GroupingStatusResponse>(`/grouping/status/${runId}`)
    return data
  },

  async getGroupingHistory(): Promise<GroupingHistoryResponse> {
    const { data } = await apiClient.get<GroupingHistoryResponse>('/grouping/history')
    return data
  },
}
