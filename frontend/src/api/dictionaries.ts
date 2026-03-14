import apiClient from './client'

export interface DictionaryItem {
  id: string
  name: string
  is_active: boolean
  created_at: string
  level?: number | null
}

export const dictionariesApi = {
  async getAll(
    type: 'directions' | 'priority_directions' | 'trl_levels',
    activeOnly = true,
  ): Promise<DictionaryItem[]> {
    const { data } = await apiClient.get<DictionaryItem[]>(`/dictionaries/${type}`, {
      params: activeOnly ? { active_only: true } : {},
    })
    return data
  },
}
