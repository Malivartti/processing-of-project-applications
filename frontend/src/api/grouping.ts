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

  async getGroupingHistory() {
    const { data } = await apiClient.get('/grouping/history')
    return data
  },
}
