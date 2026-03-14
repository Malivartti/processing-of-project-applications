import { defineStore } from 'pinia'
import { ref, reactive } from 'vue'
import { projectsApi, type ProjectListItem, type StatsCounters } from '../api/projects'

export interface ProjectsFilters {
  search: string
  direction_id: string | null
  priority_direction_id: string | null
  trl_id: string | null
  is_ongoing: boolean | null
  has_group: boolean | null
  group_source: string | null
  page: number
  limit: number
}

export const useProjectsStore = defineStore('projects', () => {
  const items = ref<ProjectListItem[]>([])
  const total = ref(0)
  const loading = ref(false)
  const stats = ref<StatsCounters>({ total: 0, new: 0, auto_checked: 0 })

  const filters = reactive<ProjectsFilters>({
    search: '',
    direction_id: null,
    priority_direction_id: null,
    trl_id: null,
    is_ongoing: null,
    has_group: null,
    group_source: null,
    page: 1,
    limit: 50,
  })

  async function fetchProjects() {
    loading.value = true
    try {
      const result = await projectsApi.getList({
        search: filters.search || undefined,
        direction_id: filters.direction_id || undefined,
        priority_direction_id: filters.priority_direction_id || undefined,
        trl_id: filters.trl_id || undefined,
        is_ongoing: filters.is_ongoing ?? undefined,
        has_group: filters.has_group ?? undefined,
        group_source: filters.group_source || undefined,
        limit: filters.limit,
        offset: (filters.page - 1) * filters.limit,
      })
      items.value = result.items
      total.value = result.total
    } finally {
      loading.value = false
    }
  }

  async function fetchStats() {
    stats.value = await projectsApi.getStats()
  }

  function setFilters(newFilters: Partial<ProjectsFilters>) {
    Object.assign(filters, newFilters, { page: 1 })
  }

  function setPage(page: number) {
    filters.page = page
  }

  function resetFilters() {
    Object.assign(filters, {
      search: '',
      direction_id: null,
      priority_direction_id: null,
      trl_id: null,
      is_ongoing: null,
      has_group: null,
      group_source: null,
      page: 1,
    })
  }

  return {
    items,
    total,
    loading,
    stats,
    filters,
    fetchProjects,
    fetchStats,
    setFilters,
    setPage,
    resetFilters,
  }
})
