import apiClient from './client'

export interface DictionaryItem {
  id: string
  name: string
  is_active: boolean
  created_at: string
  level?: number | null
}

export type DictionaryType = 'directions' | 'priority_directions' | 'trl_levels'

export const dictionariesApi = {
  async getAll(type: DictionaryType, activeOnly = true): Promise<DictionaryItem[]> {
    const { data } = await apiClient.get<DictionaryItem[]>(`/dictionaries/${type}`, {
      params: activeOnly ? { active_only: true } : {},
    })
    return data
  },

  async create(type: DictionaryType, name: string, level?: number | null): Promise<DictionaryItem> {
    const { data } = await apiClient.post<DictionaryItem>(`/dictionaries/${type}`, { name, level })
    return data
  },

  async update(
    type: DictionaryType,
    id: string,
    name: string,
    level?: number | null,
  ): Promise<DictionaryItem> {
    const { data } = await apiClient.patch<DictionaryItem>(`/dictionaries/${type}/${id}`, {
      name,
      level,
    })
    return data
  },

  async deactivate(type: DictionaryType, id: string): Promise<void> {
    await apiClient.delete(`/dictionaries/${type}/${id}`)
  },
}
