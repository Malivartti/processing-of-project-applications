import apiClient from './client'

export interface ProjectListItem {
  id: string
  title: string
  is_ongoing: boolean
  is_selected: boolean
  is_auto_checked: boolean
  source: string
  direction_id: string | null
  direction_name: string | null
  priority_direction_id: string | null
  trl_id: string | null
  group_id: string | null
  group_name: string | null
  group_source: string | null
  created_at: string
}

export interface ProjectListResponse {
  items: ProjectListItem[]
  total: number
}

export interface StatsCounters {
  total: number
  new: number
  auto_checked: number
}

export interface ProjectFilters {
  search?: string
  direction_id?: string
  priority_direction_id?: string
  trl_id?: string
  is_ongoing?: boolean
  has_group?: boolean
  group_source?: string
  limit?: number
  offset?: number
}

export interface GroupInfo {
  id: string
  name: string
  source: string
  context: string
  is_confirmed: boolean
}

export interface ProjectRead {
  id: string
  title: string
  problem: string | null
  goal: string | null
  expected_result: string | null
  is_ongoing: boolean
  is_selected: boolean
  is_auto_checked: boolean
  source: string
  direction_id: string | null
  direction_name: string | null
  priority_direction_id: string | null
  priority_direction_name: string | null
  trl_id: string | null
  trl_name: string | null
  group: GroupInfo | null
  created_at: string
  updated_at: string
}

export const projectsApi = {
  async getList(filters: ProjectFilters = {}): Promise<ProjectListResponse> {
    const params: Record<string, unknown> = {
      limit: filters.limit ?? 50,
      offset: filters.offset ?? 0,
    }
    if (filters.search) params.search = filters.search
    if (filters.direction_id) params.direction_id = filters.direction_id
    if (filters.priority_direction_id) params.priority_direction_id = filters.priority_direction_id
    if (filters.trl_id) params.trl_id = filters.trl_id
    if (filters.is_ongoing !== undefined) params.is_ongoing = filters.is_ongoing
    if (filters.has_group !== undefined) params.has_group = filters.has_group
    if (filters.group_source) params.group_source = filters.group_source

    const { data } = await apiClient.get<ProjectListResponse>('/projects', { params })
    return data
  },

  async getStats(): Promise<StatsCounters> {
    const { data } = await apiClient.get<StatsCounters>('/stats/counters')
    return data
  },

  async select(id: string): Promise<void> {
    await apiClient.post(`/projects/${id}/select`)
  },

  async deselect(id: string): Promise<void> {
    await apiClient.delete(`/projects/${id}/select`)
  },

  async getById(id: string): Promise<ProjectRead> {
    const { data } = await apiClient.get<ProjectRead>(`/projects/${id}`)
    return data
  },
}
