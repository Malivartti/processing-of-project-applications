import apiClient from './client'

export interface GroupProjectItem {
  id: string
  title: string
}

export interface GroupRead {
  id: string
  name: string
  description: string | null
  source: string
  context: string
  is_confirmed: boolean
  created_at: string
  updated_at: string
  projects: GroupProjectItem[]
}

export interface GroupListItem {
  id: string
  name: string
  description: string | null
  source: string
  context: string
  is_confirmed: boolean
  project_count: number
  created_at: string
  updated_at: string
}

export interface GroupListResponse {
  items: GroupListItem[]
  total: number
}

export interface GroupCreate {
  name: string
  description?: string | null
  project_ids: string[]
  context?: string
}

export interface ConflictingProject {
  project_id: string
  group_id: string
  group_name: string
}

export const groupsApi = {
  async getAll(params: {
    source?: string
    context?: string
    is_confirmed?: boolean
  } = {}): Promise<GroupListResponse> {
    const { data } = await apiClient.get<GroupListResponse>('/groups', { params })
    return data
  },

  async getById(id: string): Promise<GroupRead> {
    const { data } = await apiClient.get<GroupRead>(`/groups/${id}`)
    return data
  },

  async create(body: GroupCreate): Promise<GroupRead> {
    const { data } = await apiClient.post<GroupRead>('/groups', body)
    return data
  },

  async update(id: string, body: { name?: string; description?: string | null }): Promise<GroupRead> {
    const { data } = await apiClient.patch<GroupRead>(`/groups/${id}`, body)
    return data
  },

  async delete(id: string): Promise<void> {
    await apiClient.delete(`/groups/${id}`)
  },

  async confirm(id: string): Promise<GroupRead> {
    const { data } = await apiClient.post<GroupRead>(`/groups/${id}/confirm`)
    return data
  },

  async removeProject(groupId: string, projectId: string): Promise<GroupRead> {
    const { data } = await apiClient.delete<GroupRead>(`/groups/${groupId}/projects/${projectId}`)
    return data
  },
}
