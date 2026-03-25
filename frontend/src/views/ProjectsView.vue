<template>
  <div class="projects-view">
    <ProjectDetailPanel
      :project-id="selectedProjectId"
      :search-keywords="searchKeywords"
      @close="selectedProjectId = null"
      @updated="onPanelUpdated"
      @navigate="selectedProjectId = $event"
      @compare="onCompareFromPanel"
    />

    <CreateGroupDialog
      v-model="showCreateGroup"
      :selected-projects="checkedRows"
      @created="onGroupCreated"
    />

    <GroupingRunDialog
      v-model="showGroupingDialog"
      @start="onGroupingStart"
    />

    <ProjectImportDialog
      v-model="showImportDialog"
      @imported="onImported"
    />

    <ComparisonSideBySide
      v-model="showCompare"
      :project-ids="compareIds"
    />

    <!-- Stats header -->
    <el-row :gutter="16" class="stats-row">
      <el-col :span="8">
        <el-statistic title="Всего проектов" :value="store.stats.total" />
      </el-col>
      <el-col :span="8">
        <el-statistic title="Новых" :value="store.stats.new" />
      </el-col>
      <el-col :span="8">
        <el-statistic title="Авто-проверенных" :value="store.stats.auto_checked" />
      </el-col>
    </el-row>

    <el-divider />

    <!-- Filters -->
    <ProjectFilters :initial-filters="store.filters" @change="onFiltersChange" @reset="onFiltersReset" />

    <!-- Actions toolbar -->
    <div class="toolbar">
      <div class="toolbar-right">
        <GroupingProgressBar
          v-if="activeRunId"
          :run-id="activeRunId"
          context="main"
          @completed="onGroupingCompleted"
          @error="onGroupingError"
        />
        <template v-else>
          <el-button size="small" @click="showImportDialog = true">Импорт</el-button>
          <el-button
            size="small"
            type="warning"
            plain
            :loading="clearingAutoGroups"
            @click="clearAutoGroups"
          >
            Очистить авто группы
          </el-button>
          <el-button
            size="small"
            type="danger"
            plain
            :loading="clearingAll"
            @click="clearAllProjects"
          >
            Очистить все
          </el-button>
          <el-button
            type="primary"
            size="small"
            @click="showGroupingDialog = true"
          >
            Найти похожие
          </el-button>
        </template>
        <el-radio-group :model-value="store.viewMode" size="small" class="view-toggle" @change="onViewModeChange">
          <el-radio-button value="list">Список</el-radio-button>
          <el-radio-button value="groups">Группы</el-radio-button>
        </el-radio-group>
      </div>
    </div>

    <!-- List mode: Table -->
    <template v-if="store.viewMode === 'list'">
      <el-table
        ref="tableRef"
        v-loading="store.loading"
        :data="store.items"
        style="width: 100%; margin-top: 12px"
        stripe
        highlight-current-row
        @row-click="onRowClick"
        @selection-change="onSelectionChange"
      >
        <el-table-column type="selection" width="48" @click.stop />

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

        <el-table-column label="Группа" width="180">
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

        <el-table-column label="Статус" width="120" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.is_selected" type="warning" size="small">В отборе</el-tag>
            <el-tag v-else-if="row.is_auto_checked" type="success" size="small">Проверен</el-tag>
            <el-tag v-else type="info" size="small">Новый</el-tag>
          </template>
        </el-table-column>
      </el-table>

      <!-- Pagination -->
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

    <!-- Groups mode: Accordion -->
    <GroupsAccordion
      v-else
      :items="store.groupModeItems"
      :groups="store.groups"
      :loading="store.groupModeLoading"
      @project-click="onProjectClick"
      @refresh="onGroupsRefresh"
    />

    <!-- Floating action panel (list mode only) -->
    <transition name="float-panel">
      <div v-if="store.viewMode === 'list' && checkedRows.length >= 1" class="float-actions">
        <span class="float-label">Выбрано: {{ checkedRows.length }}</span>
        <el-button
          v-if="checkedRows.length === 2"
          size="small"
          @click="openCompare"
        >
          Сравнить
        </el-button>
        <el-button v-if="checkedRows.length >= 2" type="primary" size="small" @click="openCreateGroup">Создать группу</el-button>
        <el-button size="small" @click="addToSelection">Добавить в отбор</el-button>
        <el-button size="small" @click="clearChecked">Сбросить</el-button>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { TableInstance } from 'element-plus'
import { useProjectsStore, type ProjectsFilters, type ViewMode } from '../stores/projects'
import { projectsApi, type ProjectListItem } from '../api/projects'
import { groupingApi } from '../api/grouping'
import { groupsApi } from '../api/groups'
import ProjectFilters from '../components/ProjectFilters.vue'
import ProjectDetailPanel from '../components/ProjectDetailPanel.vue'
import CreateGroupDialog from '../components/CreateGroupDialog.vue'
import GroupsAccordion from '../components/GroupsAccordion.vue'
import GroupingRunDialog from '../components/GroupingRunDialog.vue'
import GroupingProgressBar from '../components/GroupingProgressBar.vue'
import ProjectImportDialog from '../components/ProjectImportDialog.vue'
import ComparisonSideBySide from '../components/ComparisonSideBySide.vue'

const route = useRoute()
const router = useRouter()
const store = useProjectsStore()

const currentPage = ref(store.filters.page)
const pageSize = ref(store.filters.limit)
const tableRef = ref<TableInstance>()

// Checked rows (for mass actions)
const checkedRows = ref<ProjectListItem[]>([])
const showCreateGroup = ref(false)
const showGroupingDialog = ref(false)
const showImportDialog = ref(false)
const showCompare = ref(false)
const compareIds = ref<[string, string] | null>(null)
const activeRunId = ref<string | null>(null)
const clearingAll = ref(false)
const clearingAutoGroups = ref(false)

function onSelectionChange(rows: ProjectListItem[]) {
  checkedRows.value = rows
}

function openCreateGroup() {
  showCreateGroup.value = true
}

function clearChecked() {
  tableRef.value?.clearSelection()
}

function openCompare() {
  if (checkedRows.value.length !== 2) return
  compareIds.value = [checkedRows.value[0].id, checkedRows.value[1].id]
  showCompare.value = true
}

function onCompareFromPanel(otherId: string) {
  if (!selectedProjectId.value) return
  compareIds.value = [selectedProjectId.value, otherId]
  showCompare.value = true
}

async function addToSelection() {
  const ids = checkedRows.value.map((r) => r.id)
  try {
    await Promise.all(ids.map((id) => projectsApi.select(id)))
    ElMessage.success(`Добавлено в отбор: ${ids.length}`)
    clearChecked()
    store.fetchProjects()
    store.fetchStats()
  } catch {
    // axios interceptor handles toast
  }
}

async function onGroupingStart(threshold: number) {
  try {
    const res = await groupingApi.startGrouping(threshold, 'main')
    activeRunId.value = res.run_id
  } catch {
    // axios interceptor handles toast
  }
}

function onGroupingCompleted(groupsFound: number) {
  activeRunId.value = null
  ElMessage.success(`Группировка завершена: найдено ${groupsFound} групп`)
  store.fetchProjects()
  store.fetchStats()
  if (store.viewMode === 'groups') {
    store.fetchGroupsMode()
  }
}

function onGroupingError(message: string) {
  activeRunId.value = null
  ElMessage.error(message)
}

function onImported() {
  store.fetchProjects()
  store.fetchStats()
}

async function clearAutoGroups() {
  try {
    await ElMessageBox.confirm(
      'Будут удалены все авто группы. Проекты останутся в системе. Продолжить?',
      'Очистить авто группы',
      {
        confirmButtonText: 'Удалить',
        cancelButtonText: 'Отмена',
        type: 'warning',
        confirmButtonClass: 'el-button--danger',
      },
    )
  } catch {
    return
  }
  clearingAutoGroups.value = true
  try {
    const deleted = await groupsApi.deleteAllAuto('main')
    ElMessage.success(`Удалено авто групп: ${deleted}`)
    store.fetchProjects()
    store.fetchStats()
    if (store.viewMode === 'groups') store.fetchGroupsMode()
  } catch {
    // axios interceptor handles toast
  } finally {
    clearingAutoGroups.value = false
  }
}

async function clearAllProjects() {
  try {
    await ElMessageBox.confirm(
      'Будут удалены все проекты, группы и результаты группировки. Это действие необратимо. Продолжить?',
      'Очистить все проекты',
      {
        confirmButtonText: 'Удалить всё',
        cancelButtonText: 'Отмена',
        type: 'warning',
        confirmButtonClass: 'el-button--danger',
      },
    )
  } catch {
    return
  }
  clearingAll.value = true
  try {
    const deleted = await projectsApi.deleteAll()
    ElMessage.success(`Удалено проектов: ${deleted}`)
    clearChecked()
    store.fetchProjects()
    store.fetchStats()
    if (store.viewMode === 'groups') store.fetchGroupsMode()
  } catch {
    // axios interceptor handles toast
  } finally {
    clearingAll.value = false
  }
}

async function onGroupCreated() {
  clearChecked()
  store.fetchProjects()
  store.fetchStats()
}

// Group color palette
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

function syncFiltersFromQuery() {
  const q = route.query
  const updates: Partial<ProjectsFilters> = {}
  if (q.search) updates.search = String(q.search)
  if (q.direction_id) updates.direction_id = String(q.direction_id)
  if (q.priority_direction_id) updates.priority_direction_id = String(q.priority_direction_id)
  if (q.trl_id) updates.trl_id = String(q.trl_id)
  if (q.is_ongoing !== undefined) updates.is_ongoing = q.is_ongoing === 'true'
  if (q.has_group !== undefined) updates.has_group = q.has_group === 'true'
  if (q.group_source) updates.group_source = String(q.group_source)
  if (q.page) updates.page = Number(q.page)
  if (q.limit) updates.limit = Number(q.limit)

  if (Object.keys(updates).length) {
    Object.assign(store.filters, updates)
    currentPage.value = store.filters.page
    pageSize.value = store.filters.limit
  }
}

function syncQueryFromFilters() {
  const query: Record<string, string> = {}
  const f = store.filters
  if (f.search) query.search = f.search
  if (f.direction_id) query.direction_id = f.direction_id
  if (f.priority_direction_id) query.priority_direction_id = f.priority_direction_id
  if (f.trl_id) query.trl_id = f.trl_id
  if (f.is_ongoing !== null) query.is_ongoing = String(f.is_ongoing)
  if (f.has_group !== null) query.has_group = String(f.has_group)
  if (f.group_source) query.group_source = f.group_source
  if (f.page > 1) query.page = String(f.page)
  if (f.limit !== 50) query.limit = String(f.limit)

  router.replace({ query })
}

function onFiltersChange(newFilters: Partial<ProjectsFilters>) {
  store.setFilters(newFilters)
  currentPage.value = 1
  syncQueryFromFilters()
  store.fetchProjects()
  if (store.viewMode === 'groups') store.fetchGroupsMode()
}

function onFiltersReset() {
  store.resetFilters()
  currentPage.value = 1
  pageSize.value = 50
  router.replace({ query: {} })
  store.fetchProjects()
  if (store.viewMode === 'groups') store.fetchGroupsMode()
}

function onPageChange(page: number) {
  store.setPage(page)
  syncQueryFromFilters()
  store.fetchProjects()
}

function onSizeChange(size: number) {
  store.setFilters({ limit: size, page: 1 })
  currentPage.value = 1
  syncQueryFromFilters()
  store.fetchProjects()
}

const selectedProjectId = ref<string | null>(null)
const searchKeywords = computed(() =>
  store.filters.search?.split(/\s+/).filter(Boolean) ?? []
)

function onRowClick(row: { id: string }) {
  selectedProjectId.value = row.id
}

function onProjectClick(id: string) {
  selectedProjectId.value = id
}

function onPanelUpdated() {
  store.fetchProjects()
  store.fetchStats()
  if (store.viewMode === 'groups') {
    store.fetchGroupsMode()
  }
}

function onGroupsRefresh() {
  store.fetchGroupsMode()
  store.fetchProjects()
  store.fetchStats()
}

function onViewModeChange(mode: ViewMode) {
  store.setViewMode(mode)
  if (mode === 'groups') {
    store.fetchGroupsMode()
  }
}

onMounted(() => {
  syncFiltersFromQuery()
  Promise.all([store.fetchProjects(), store.fetchStats()])
  if (store.viewMode === 'groups') {
    store.fetchGroupsMode()
  }
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
.projects-view {
  padding: 0 4px;
}

.stats-row {
  margin-bottom: 8px;
}

.toolbar {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 4px;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
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

.float-actions {
  position: fixed;
  bottom: 32px;
  left: 50%;
  transform: translateX(-50%);
  background: #fff;
  border: 1px solid #dcdfe6;
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
  padding: 10px 20px;
  display: flex;
  align-items: center;
  gap: 12px;
  z-index: 100;
}

.float-label {
  font-size: 14px;
  color: #606266;
  font-weight: 500;
}

.float-panel-enter-active,
.float-panel-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.float-panel-enter-from,
.float-panel-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(16px);
}
</style>
