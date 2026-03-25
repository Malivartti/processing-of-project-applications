<template>
  <div class="selection-view">
    <ProjectDetailPanel
      :project-id="selectedProjectId"
      :search-keywords="searchKeywords"
      @close="selectedProjectId = null"
      @updated="onPanelUpdated"
    />

    <GroupingRunDialog
      v-model="showGroupingDialog"
      @start="onGroupingStart"
    />

    <!-- Header -->
    <el-row :gutter="16" class="stats-row">
      <el-col :span="8">
        <el-statistic title="Отобрано проектов" :value="store.total" />
      </el-col>
    </el-row>

    <el-divider />

    <!-- Filters + toolbar -->
    <div class="toolbar">
      <ProjectFilters
        :initial-filters="selectionFilters"
        @change="onFiltersChange"
        @reset="onFiltersReset"
      />
      <div class="toolbar-right">
        <GroupingProgressBar
          v-if="activeRunId"
          :run-id="activeRunId"
          context="selection"
          @completed="onGroupingCompleted"
          @error="onGroupingError"
        />
        <template v-else>
          <el-button size="small" @click="exportSelected">Экспорт в Excel</el-button>
          <el-button
            type="primary"
            size="small"
            @click="showGroupingDialog = true"
          >
            Проверить на схожесть
          </el-button>
        </template>
        <el-radio-group :model-value="store.viewMode" size="small" class="view-toggle" @change="onViewModeChange">
          <el-radio-button value="list">Список</el-radio-button>
          <el-radio-button value="groups">Группы</el-radio-button>
        </el-radio-group>
      </div>
    </div>

    <!-- List mode -->
    <template v-if="store.viewMode === 'list'">
      <el-table
        v-loading="store.loading"
        :data="store.items"
        style="width: 100%; margin-top: 12px"
        stripe
        highlight-current-row
        @row-click="onRowClick"
      >
        <el-table-column prop="title" label="Название" min-width="280" show-overflow-tooltip />

        <el-table-column label="Направление" width="200" show-overflow-tooltip>
          <template #default="{ row }">
            <span>{{ row.direction_name || '—' }}</span>
          </template>
        </el-table-column>


        <el-table-column label="Реализуется" width="110" align="center">
          <template #default="{ row }">
            <span>{{ row.is_ongoing ? 'Да' : 'Нет' }}</span>
          </template>
        </el-table-column>

        <el-table-column label="Группа (отбор)" width="180">
          <template #default="{ row }">
            <el-tag
              v-if="row.group_name"
              :color="getGroupColor(row.group_id)"
              :style="groupTagStyle(row)"
              size="small"
              effect="plain"
            >
              {{ row.group_name }}
            </el-tag>
            <span v-else>—</span>
          </template>
        </el-table-column>

        <el-table-column label="Действия" width="140" align="center">
          <template #default="{ row }">
            <el-button
              size="small"
              type="danger"
              plain
              :loading="removingId === row.id"
              @click.stop="removeFromSelection(row.id)"
            >
              Убрать
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="store.total"
          :page-sizes="[25, 50, 100]"
          layout="total, sizes, prev, pager, next"
          background
          @current-change="onPageChange"
          @size-change="onSizeChange"
        />
      </div>
    </template>

    <!-- Groups mode -->
    <GroupsAccordion
      v-else
      :items="store.groupModeItems"
      :groups="store.groups"
      :loading="store.groupModeLoading"
      @project-click="onProjectClick"
      @refresh="onGroupsRefresh"
    />

    <el-empty
      v-if="!store.loading && store.total === 0 && store.viewMode === 'list'"
      description="Нет отобранных проектов. Добавьте проекты в отбор из вкладки «Проекты»."
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { useSelectionStore, type SelectionViewMode } from '../stores/selection'
import { projectsApi } from '../api/projects'
import { groupingApi } from '../api/grouping'
import ProjectFilters from '../components/ProjectFilters.vue'
import ProjectDetailPanel from '../components/ProjectDetailPanel.vue'
import GroupsAccordion from '../components/GroupsAccordion.vue'
import GroupingRunDialog from '../components/GroupingRunDialog.vue'
import GroupingProgressBar from '../components/GroupingProgressBar.vue'

const store = useSelectionStore()

const searchKeywords = computed(() =>
  store.filters.search?.split(/\s+/).filter(Boolean) ?? []
)

const currentPage = ref(store.filters.page)
const pageSize = ref(store.filters.limit)
const selectedProjectId = ref<string | null>(null)
const removingId = ref<string | null>(null)
const showGroupingDialog = ref(false)
const activeRunId = ref<string | null>(null)

// Adapter for ProjectFilters component (subset without group filters)
const selectionFilters = computed(() => ({
  search: store.filters.search,
  direction_id: store.filters.direction_id,
  priority_direction_id: store.filters.priority_direction_id,
  trl_id: store.filters.trl_id,
  is_ongoing: store.filters.is_ongoing,
  has_group: null,
  group_source: null,
  page: store.filters.page,
  limit: store.filters.limit,
}))

async function removeFromSelection(id: string) {
  removingId.value = id
  try {
    await projectsApi.deselect(id)
    ElMessage.success('Проект убран из отбора')
    await store.fetchProjects()
    if (store.viewMode === 'groups') store.fetchGroupsMode()
  } catch {
    // axios interceptor handles toast
  } finally {
    removingId.value = null
  }
}

function exportSelected() {
  const url = projectsApi.exportUrl('selected')
  window.open(url, '_blank')
}

async function onGroupingStart(threshold: number) {
  try {
    const res = await groupingApi.startGrouping(threshold, 'selection')
    activeRunId.value = res.run_id
  } catch {
    // axios interceptor handles toast
  }
}

function onGroupingCompleted(groupsFound: number) {
  activeRunId.value = null
  ElMessage.success(`Проверка завершена: найдено ${groupsFound} групп`)
  store.fetchProjects()
  if (store.viewMode === 'groups') {
    store.fetchGroupsMode()
  }
}

function onGroupingError(message: string) {
  activeRunId.value = null
  ElMessage.error(message)
}

function onFiltersChange(newFilters: Record<string, unknown>) {
  store.setFilters(newFilters as Parameters<typeof store.setFilters>[0])
  currentPage.value = 1
  store.fetchProjects()
  if (store.viewMode === 'groups') store.fetchGroupsMode()
}

function onFiltersReset() {
  store.resetFilters()
  currentPage.value = 1
  pageSize.value = 50
  store.fetchProjects()
  if (store.viewMode === 'groups') store.fetchGroupsMode()
}

function onPageChange(page: number) {
  store.setPage(page)
  store.fetchProjects()
}

function onSizeChange(size: number) {
  store.setFilters({ limit: size, page: 1 })
  currentPage.value = 1
  store.fetchProjects()
}

function onRowClick(row: { id: string }) {
  selectedProjectId.value = row.id
}

function onProjectClick(id: string) {
  selectedProjectId.value = id
}

function onPanelUpdated() {
  store.fetchProjects()
  if (store.viewMode === 'groups') store.fetchGroupsMode()
}

function onGroupsRefresh() {
  store.fetchGroupsMode()
  store.fetchProjects()
}

function onViewModeChange(mode: SelectionViewMode) {
  store.setViewMode(mode)
  if (mode === 'groups') store.fetchGroupsMode()
}

// Group color helpers (same palette as ProjectsView)
const GROUP_COLORS = [
  '#ecf5ff', '#f0f9eb', '#fdf6ec', '#fef0f0',
  '#f4f4f5', '#e8f4f8', '#fef9e7', '#f5f0ff',
]

function getGroupColor(groupId: string | null): string {
  if (!groupId) return '#f4f4f5'
  let hash = 0
  for (let i = 0; i < groupId.length; i++) {
    hash = (hash << 5) - hash + groupId.charCodeAt(i)
    hash |= 0
  }
  return GROUP_COLORS[Math.abs(hash) % GROUP_COLORS.length]
}

function groupTagStyle(row: { group_source: string | null }) {
  return {
    border: row.group_source === 'auto' ? '1px dashed #909399' : '1px solid #909399',
    color: '#606266',
  }
}

onMounted(() => {
  store.fetchProjects()
  if (store.viewMode === 'groups') store.fetchGroupsMode()
})

watch(
  () => store.filters.page,
  (p) => (currentPage.value = p),
)
watch(
  () => store.filters.limit,
  (l) => (pageSize.value = l),
)
</script>

<style scoped>
.selection-view {
  padding: 0 4px;
}

.stats-row {
  margin-bottom: 8px;
}

.toolbar {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.view-toggle {
  flex-shrink: 0;
  margin-top: 2px;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
