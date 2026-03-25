<template>
  <div v-loading="loading" class="groups-accordion">
    <!-- Groups -->
    <el-collapse v-model="openGroups">
      <el-collapse-item
        v-for="group in groupedData"
        :key="group.id"
        :name="group.id"
      >
        <template #title>
          <div class="group-header" @click.stop>
            <!-- Inline edit form -->
            <template v-if="editingGroupId === group.id">
              <el-input
                v-model="editName"
                size="small"
                placeholder="Название группы"
                style="width: 200px"
                @click.stop
              />
              <el-input
                v-model="editDescription"
                size="small"
                placeholder="Описание (опционально)"
                style="width: 200px"
                @click.stop
              />
              <el-button
                type="primary"
                size="small"
                :loading="savingGroupId === group.id"
                @click.stop="saveEdit(group.id)"
              >
                Сохранить
              </el-button>
              <el-button size="small" @click.stop="cancelEdit">Отмена</el-button>
            </template>

            <!-- Normal view -->
            <template v-else>
              <el-tag
                :color="getGroupColor(group.id)"
                :style="groupTagStyle(group)"
                size="small"
                effect="plain"
                class="group-name-tag"
                @click.stop="toggleGroup(group.id)"
              >
                {{ group.name }}
              </el-tag>
              <span class="group-meta">
                <span class="group-count">{{ group.projects.length }} проектов</span>
                <el-tag
                  :type="group.source === 'auto' ? 'info' : 'success'"
                  size="small"
                  effect="plain"
                >
                  {{ group.source === 'auto' ? 'Авто' : 'Ручная' }}
                </el-tag>
                <el-tag
                  v-if="group.is_confirmed"
                  type="success"
                  size="small"
                  effect="plain"
                >
                  Подтверждена
                </el-tag>
                <el-tag
                  v-else-if="group.source === 'auto'"
                  type="warning"
                  size="small"
                  effect="plain"
                >
                  Не подтверждена
                </el-tag>
              </span>

              <!-- Action buttons -->
              <div class="group-actions" @click.stop>
                <el-tooltip v-if="group.projects.length === 2" content="Сравнить проекты" placement="top">
                  <el-button
                    text
                    size="small"
                    :icon="CompareIcon"
                    @click.stop="openGroupCompare(group.projects)"
                  />
                </el-tooltip>
                <el-tooltip content="Редактировать" placement="top">
                  <el-button
                    text
                    size="small"
                    :icon="EditIcon"
                    @click.stop="startEdit(group)"
                  />
                </el-tooltip>
                <el-tooltip v-if="!group.is_confirmed" content="Подтвердить группу" placement="top">
                  <el-button
                    text
                    size="small"
                    :icon="CheckIcon"
                    type="success"
                    :loading="confirmingGroupId === group.id"
                    @click.stop="confirmGroup(group.id)"
                  />
                </el-tooltip>
                <el-tooltip content="Удалить группу" placement="top">
                  <el-button
                    text
                    size="small"
                    :icon="DeleteIcon"
                    type="danger"
                    :loading="deletingGroupId === group.id"
                    @click.stop="deleteGroup(group.id, group.name)"
                  />
                </el-tooltip>
              </div>
            </template>
          </div>
        </template>

        <div class="group-projects">
          <div
            v-for="project in group.projects"
            :key="project.id"
            class="project-row"
            :class="{ 'project-row--checked': checkedIds.has(project.id) }"
            @click="$emit('project-click', project.id)"
          >
            <el-checkbox
              :model-value="checkedIds.has(project.id)"
              @click.stop
              @change="toggleCheck(project.id)"
            />
            <span class="project-title">{{ project.title }}</span>
            <div class="project-tags">
              <el-tag v-if="project.direction_name" size="small" effect="plain" type="info">
                {{ project.direction_name }}
              </el-tag>
              <el-tag v-if="project.is_selected" type="warning" size="small">В отборе</el-tag>
              <el-tag v-else-if="project.is_auto_checked" type="success" size="small">Проверен</el-tag>
              <el-tag v-else type="info" size="small">Новый</el-tag>
            </div>
          </div>
        </div>
      </el-collapse-item>
    </el-collapse>

    <!-- Ungrouped projects -->
    <el-collapse v-if="ungroupedProjects.length > 0" v-model="openUngrouped">
      <el-collapse-item name="ungrouped">
        <template #title>
          <div class="group-header">
            <span class="ungrouped-label">Без группы</span>
            <span class="group-count">{{ ungroupedProjects.length }} проектов</span>
          </div>
        </template>
        <div class="group-projects">
          <div
            v-for="project in ungroupedProjects"
            :key="project.id"
            class="project-row"
            :class="{ 'project-row--checked': checkedIds.has(project.id) }"
            @click="$emit('project-click', project.id)"
          >
            <el-checkbox
              :model-value="checkedIds.has(project.id)"
              @click.stop
              @change="toggleCheck(project.id)"
            />
            <span class="project-title">{{ project.title }}</span>
            <div class="project-tags">
              <el-tag v-if="project.direction_name" size="small" effect="plain" type="info">
                {{ project.direction_name }}
              </el-tag>
              <el-tag v-if="project.is_selected" type="warning" size="small">В отборе</el-tag>
              <el-tag v-else-if="project.is_auto_checked" type="success" size="small">Проверен</el-tag>
              <el-tag v-else type="info" size="small">Новый</el-tag>
            </div>
          </div>
        </div>
      </el-collapse-item>
    </el-collapse>

    <el-empty v-if="!loading && groupedData.length === 0 && ungroupedProjects.length === 0" description="Нет данных" />

    <!-- Floating action panel -->
    <transition name="float-panel">
      <div v-if="checkedIds.size >= 1" class="float-actions">
        <span class="float-label">Выбрано: {{ checkedIds.size }}</span>
        <el-button
          size="small"
          type="primary"
          :loading="addingToSelection"
          @click="addToSelection"
        >Добавить в отбор</el-button>
        <el-button v-if="canCreateGroup" size="small" @click="showCreateGroup = true">Создать группу</el-button>
        <AddToGroupPopover
          :project-ids="Array.from(checkedIds)"
          context="main"
          @done="() => { checkedIds.clear(); emit('refresh') }"
        />
        <el-button v-if="checkedIds.size === 2" size="small" @click="openCompare">Сравнить</el-button>
        <el-button size="small" @click="checkedIds.clear()">Сбросить</el-button>
      </div>
    </transition>

    <ComparisonSideBySide
      v-model="showCompare"
      :project-ids="compareIds"
    />

    <CreateGroupDialog
      v-model="showCreateGroup"
      :selected-projects="checkedProjects"
      @created="() => { checkedIds.clear(); emit('refresh') }"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, markRaw, reactive } from 'vue'
import { ElMessageBox, ElMessage } from 'element-plus'
import { Edit, Check, Delete, ScaleToOriginal } from '@element-plus/icons-vue'
import type { ProjectListItem } from '../api/projects'
import { projectsApi } from '../api/projects'
import type { GroupListItem } from '../api/groups'
import { groupsApi } from '../api/groups'
import ComparisonSideBySide from './ComparisonSideBySide.vue'
import CreateGroupDialog from './CreateGroupDialog.vue'
import AddToGroupPopover from './AddToGroupPopover.vue'

const EditIcon = markRaw(Edit)
const CheckIcon = markRaw(Check)
const DeleteIcon = markRaw(Delete)
const CompareIcon = markRaw(ScaleToOriginal)

const props = defineProps<{
  items: ProjectListItem[]
  groups: GroupListItem[]
  loading: boolean
}>()

const emit = defineEmits<{
  (e: 'project-click', id: string): void
  (e: 'refresh'): void
  (e: 'selection-changed'): void
}>()

const openGroups = ref<string[]>([])
const openUngrouped = ref<string[]>(['ungrouped'])

// Compare selection
const checkedIds = reactive(new Set<string>())
const showCompare = ref(false)
const compareIds = ref<[string, string] | null>(null)

function toggleCheck(id: string) {
  if (checkedIds.has(id)) {
    checkedIds.delete(id)
  } else {
    checkedIds.add(id)
  }
}

function openCompare() {
  const [a, b] = Array.from(checkedIds)
  compareIds.value = [a, b]
  showCompare.value = true
}

function openGroupCompare(projects: { id: string }[]) {
  compareIds.value = [projects[0].id, projects[1].id]
  showCompare.value = true
}

// Checked projects as full objects
const checkedProjects = computed(() =>
  props.items.filter(p => checkedIds.has(p.id))
)

// Show "Создать группу" only when all checked projects are not in any group
const canCreateGroup = computed(() =>
  checkedIds.size >= 2 && checkedProjects.value.every(p => !p.group_id)
)

const showCreateGroup = ref(false)

const addingToSelection = ref(false)

async function addToSelection() {
  addingToSelection.value = true
  try {
    await Promise.all(Array.from(checkedIds).map(id => projectsApi.select(id)))
    ElMessage.success(`Добавлено в отбор: ${checkedIds.size}`)
    checkedIds.clear()
    emit('selection-changed')
  } catch {
    // axios interceptor handles toast
  } finally {
    addingToSelection.value = false
  }
}

// Edit state
const editingGroupId = ref<string | null>(null)
const editName = ref('')
const editDescription = ref('')
const savingGroupId = ref<string | null>(null)
const confirmingGroupId = ref<string | null>(null)
const deletingGroupId = ref<string | null>(null)

const GROUP_COLORS = [
  '#ecf5ff', '#f0f9eb', '#fdf6ec', '#fef0f0',
  '#f4f4f5', '#e8f4f8', '#fef9e7', '#f5f0ff',
  '#e8f5e9', '#fff3e0',
]

function getGroupColor(groupId: string): string {
  let hash = 0
  for (let i = 0; i < groupId.length; i++) {
    hash = (hash << 5) - hash + groupId.charCodeAt(i)
    hash |= 0
  }
  return GROUP_COLORS[Math.abs(hash) % GROUP_COLORS.length]
}

function groupTagStyle(group: { is_confirmed: boolean; source: string }) {
  return {
    border: !group.is_confirmed && group.source === 'auto'
      ? '1px dashed #909399'
      : '1px solid #909399',
    color: '#606266',
  }
}

function toggleGroup(id: string) {
  const idx = openGroups.value.indexOf(id)
  if (idx === -1) {
    openGroups.value.push(id)
  } else {
    openGroups.value.splice(idx, 1)
  }
}

function startEdit(group: { id: string; name: string; description?: string | null }) {
  editingGroupId.value = group.id
  editName.value = group.name
  editDescription.value = group.description ?? ''
}

function cancelEdit() {
  editingGroupId.value = null
  editName.value = ''
  editDescription.value = ''
}

async function saveEdit(groupId: string) {
  if (!editName.value.trim()) {
    ElMessage.warning('Название группы не может быть пустым')
    return
  }
  savingGroupId.value = groupId
  try {
    await groupsApi.update(groupId, {
      name: editName.value.trim(),
      description: editDescription.value.trim() || null,
    })
    ElMessage.success('Группа обновлена')
    cancelEdit()
    emit('refresh')
  } catch {
    // axios interceptor handles toast
  } finally {
    savingGroupId.value = null
  }
}

async function confirmGroup(groupId: string) {
  try {
    await ElMessageBox.confirm(
      'Подтверждение группы необратимо. Группа будет отмечена как подтверждённая и не будет затронута при повторной авто-группировке. Продолжить?',
      'Подтвердить группу',
      {
        confirmButtonText: 'Подтвердить',
        cancelButtonText: 'Отмена',
        type: 'warning',
      },
    )
  } catch {
    return
  }
  confirmingGroupId.value = groupId
  try {
    await groupsApi.confirm(groupId)
    ElMessage.success('Группа подтверждена')
    emit('refresh')
  } catch {
    // axios interceptor handles toast
  } finally {
    confirmingGroupId.value = null
  }
}

async function deleteGroup(groupId: string, groupName: string) {
  try {
    await ElMessageBox.confirm(
      `Удалить группу «${groupName}»? Проекты останутся в системе, но будут освобождены из группы.`,
      'Удалить группу',
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
  deletingGroupId.value = groupId
  try {
    await groupsApi.delete(groupId)
    ElMessage.success('Группа удалена')
    emit('refresh')
  } catch {
    // axios interceptor handles toast
  } finally {
    deletingGroupId.value = null
  }
}

// Map group metadata by id
const groupMetaById = computed(() => {
  const map = new Map<string, GroupListItem>()
  for (const g of props.groups) {
    map.set(g.id, g)
  }
  return map
})

// Build grouped structure from items
const groupedData = computed(() => {
  const groupMap = new Map<string, {
    id: string
    name: string
    source: string
    is_confirmed: boolean
    description: string | null
    projects: ProjectListItem[]
  }>()

  for (const item of props.items) {
    if (!item.group_id || !item.group_name) continue

    if (!groupMap.has(item.group_id)) {
      const meta = groupMetaById.value.get(item.group_id)
      groupMap.set(item.group_id, {
        id: item.group_id,
        name: item.group_name,
        source: item.group_source ?? 'manual',
        is_confirmed: meta?.is_confirmed ?? false,
        description: meta?.description ?? null,
        projects: [],
      })
    }
    groupMap.get(item.group_id)!.projects.push(item)
  }

  function groupOrder(g: { source: string; is_confirmed: boolean }) {
    if (g.source === 'manual') return 0
    if (g.is_confirmed) return 1
    return 2
  }
  return Array.from(groupMap.values()).sort((a, b) => {
    const diff = groupOrder(a) - groupOrder(b)
    if (diff !== 0) return diff
    return a.name.localeCompare(b.name)
  })
})

const ungroupedProjects = computed(() =>
  props.items.filter((p) => !p.group_id),
)
</script>

<style scoped>
.groups-accordion {
  margin-top: 12px;
}

.group-header {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
  min-width: 0;
  padding-right: 8px;
}

.group-name-tag {
  font-weight: 500;
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  cursor: pointer;
}

.group-meta {
  display: flex;
  align-items: center;
  gap: 6px;
}

.group-count {
  font-size: 13px;
  color: #909399;
}

.group-actions {
  display: flex;
  align-items: center;
  gap: 2px;
  margin-left: auto;
  opacity: 0;
  transition: opacity 0.15s;
}

.group-header:hover .group-actions {
  opacity: 1;
}

.ungrouped-label {
  font-weight: 500;
  color: #606266;
  font-size: 14px;
}

.group-projects {
  padding: 4px 0;
}

.project-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.15s;
  gap: 12px;
}

.project-row:hover {
  background: #f5f7fa;
}

.project-row--checked {
  background: #ecf5ff;
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

.project-title {
  flex: 1;
  font-size: 14px;
  color: #303133;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.project-tags {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}
</style>
