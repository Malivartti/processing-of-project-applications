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
  async getById(id: string): Promise<GroupRead> {
    const { data } = await apiClient.get<GroupRead>(`/groups/${id}`)
    return data
  },

  async create(body: GroupCreate): Promise<GroupRead> {
    const { data } = await apiClient.post<GroupRead>('/groups', body)
    return data
  },

  async removeProject(groupId: string, projectId: string): Promise<GroupRead> {
    const { data } = await apiClient.delete<GroupRead>(`/groups/${groupId}/projects/${projectId}`)
    return data
  },
}
