import { defineStore } from 'pinia'
import { ref, reactive } from 'vue'
import { projectsApi, type ProjectListItem } from '../api/projects'
import { groupsApi, type GroupListItem } from '../api/groups'

export interface SelectionFilters {
  search: string
  direction_id: string | null
  priority_direction_id: string | null
  trl_id: string | null
  is_ongoing: boolean | null
  page: number
  limit: number
}

export type SelectionViewMode = 'list' | 'groups'

export const useSelectionStore = defineStore('selection', () => {
  const items = ref<ProjectListItem[]>([])
  const total = ref(0)
  const loading = ref(false)

  const viewMode = ref<SelectionViewMode>(
    (localStorage.getItem('selection_view_mode') as SelectionViewMode) ?? 'list',
  )
  const groupModeItems = ref<ProjectListItem[]>([])
  const groupModeLoading = ref(false)
  const groups = ref<GroupListItem[]>([])

  const filters = reactive<SelectionFilters>({
    search: '',
    direction_id: null,
    priority_direction_id: null,
    trl_id: null,
    is_ongoing: null,
    page: 1,
    limit: 50,
  })

  async function fetchProjects() {
    loading.value = true
    try {
      const result = await projectsApi.getList({
        is_selected: true,
        search: filters.search || undefined,
        direction_id: filters.direction_id || undefined,
        priority_direction_id: filters.priority_direction_id || undefined,
        trl_id: filters.trl_id || undefined,
        is_ongoing: filters.is_ongoing ?? undefined,
        limit: filters.limit,
        offset: (filters.page - 1) * filters.limit,
      })
      items.value = result.items
      total.value = result.total
    } finally {
      loading.value = false
    }
  }

  function setFilters(newFilters: Partial<SelectionFilters>) {
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
      page: 1,
    })
  }

  function setViewMode(mode: SelectionViewMode) {
    viewMode.value = mode
    localStorage.setItem('selection_view_mode', mode)
  }

  async function fetchGroupsMode() {
    groupModeLoading.value = true
    try {
      const [projectsResult, groupsResult] = await Promise.all([
        projectsApi.getList({
          is_selected: true,
          search: filters.search || undefined,
          direction_id: filters.direction_id || undefined,
          priority_direction_id: filters.priority_direction_id || undefined,
          trl_id: filters.trl_id || undefined,
          is_ongoing: filters.is_ongoing ?? undefined,
          limit: 1000,
          offset: 0,
        }),
        groupsApi.getAll({ context: 'selection' }),
      ])
      groupModeItems.value = projectsResult.items
      groups.value = groupsResult.items
    } finally {
      groupModeLoading.value = false
    }
  }

  return {
    items,
    total,
    loading,
    filters,
    viewMode,
    groupModeItems,
    groupModeLoading,
    groups,
    fetchProjects,
    setFilters,
    setPage,
    resetFilters,
    setViewMode,
    fetchGroupsMode,
  }
})
