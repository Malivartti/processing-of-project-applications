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
            @click="$emit('project-click', project.id)"
          >
            <span class="project-title">{{ project.title }}</span>
            <div class="project-tags">
              <el-tag v-if="project.direction_name" size="small" effect="plain" type="info">
                {{ project.direction_name }}
              </el-tag>
              <el-tag :type="project.is_ongoing ? 'info' : 'success'" size="small">
                {{ project.is_ongoing ? 'Бессрочный' : 'Срочный' }}
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
            @click="$emit('project-click', project.id)"
          >
            <span class="project-title">{{ project.title }}</span>
            <div class="project-tags">
              <el-tag v-if="project.direction_name" size="small" effect="plain" type="info">
                {{ project.direction_name }}
              </el-tag>
              <el-tag :type="project.is_ongoing ? 'info' : 'success'" size="small">
                {{ project.is_ongoing ? 'Бессрочный' : 'Срочный' }}
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
  </div>
</template>

<script setup lang="ts">
import { ref, computed, markRaw } from 'vue'
import { ElMessageBox, ElMessage } from 'element-plus'
import { Edit, Check, Delete } from '@element-plus/icons-vue'
import type { ProjectListItem } from '../api/projects'
import type { GroupListItem } from '../api/groups'
import { groupsApi } from '../api/groups'

const EditIcon = markRaw(Edit)
const CheckIcon = markRaw(Check)
const DeleteIcon = markRaw(Delete)

const props = defineProps<{
  items: ProjectListItem[]
  groups: GroupListItem[]
  loading: boolean
}>()

const emit = defineEmits<{
  (e: 'project-click', id: string): void
  (e: 'refresh'): void
}>()

const openGroups = ref<string[]>([])
const openUngrouped = ref<string[]>(['ungrouped'])

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

  return Array.from(groupMap.values()).sort((a, b) => a.name.localeCompare(b.name))
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
