<template>
  <el-popover
    v-model:visible="visible"
    placement="top"
    :width="280"
    trigger="click"
    popper-class="add-to-group-popper"
  >
    <template #reference>
      <el-button size="small" @click="onOpen">Добавить в группу</el-button>
    </template>

    <div class="atg-content">
      <div class="atg-search-row">
        <el-input
          ref="searchInputRef"
          v-model="search"
          size="small"
          placeholder="Поиск или название новой..."
          clearable
          @keydown.enter="onEnter"
        />
        <el-tooltip content="Создать группу" placement="top">
          <el-button
            size="small"
            :icon="PlusIcon"
            :loading="creating"
            :disabled="!search.trim()"
            @click="createAndAdd"
          />
        </el-tooltip>
      </div>

      <div v-if="loadingGroups" class="atg-loading">
        <el-icon class="is-loading"><Loading /></el-icon>
      </div>

      <div v-else-if="filteredGroups.length === 0" class="atg-empty">
        {{ search.trim() ? 'Нет совпадений — нажмите + чтобы создать' : 'Нет ручных групп' }}
      </div>

      <div v-else class="atg-list">
        <div
          v-for="group in filteredGroups"
          :key="group.id"
          class="atg-item"
          :class="{ 'atg-item--loading': addingToGroupId === group.id }"
          @click="addToGroup(group.id, group.name)"
        >
          <span class="atg-item-name">{{ group.name }}</span>
          <span class="atg-item-count">{{ group.project_count }}</span>
        </div>
      </div>
    </div>
  </el-popover>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, markRaw } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Loading } from '@element-plus/icons-vue'
import type { InputInstance } from 'element-plus'
import { groupsApi, type GroupListItem } from '../api/groups'

const PlusIcon = markRaw(Plus)

const props = defineProps<{
  projectIds: string[]
  context?: string
}>()

const emit = defineEmits<{
  (e: 'done'): void
}>()

const visible = ref(false)
const search = ref('')
const groups = ref<GroupListItem[]>([])
const loadingGroups = ref(false)
const creating = ref(false)
const addingToGroupId = ref<string | null>(null)
const searchInputRef = ref<InputInstance>()

const filteredGroups = computed(() => {
  const q = search.value.trim().toLowerCase()
  if (!q) return groups.value
  return groups.value.filter(g => g.name.toLowerCase().includes(q))
})

async function onOpen() {
  search.value = ''
  loadingGroups.value = true
  try {
    const res = await groupsApi.getAll({ source: 'manual', context: props.context ?? 'main' })
    groups.value = res.items
  } finally {
    loadingGroups.value = false
  }
  await nextTick()
  searchInputRef.value?.focus()
}

async function addToGroup(groupId: string, groupName: string) {
  if (addingToGroupId.value) return
  addingToGroupId.value = groupId
  try {
    await Promise.all(props.projectIds.map(id => groupsApi.addProject(groupId, id)))
    ElMessage.success(`Добавлено в группу «${groupName}»`)
    visible.value = false
    emit('done')
  } catch {
    // axios interceptor handles toast
  } finally {
    addingToGroupId.value = null
  }
}

async function createAndAdd() {
  const name = search.value.trim()
  if (!name || creating.value) return
  creating.value = true
  try {
    const group = await groupsApi.create({
      name,
      project_ids: props.projectIds,
      context: props.context ?? 'main',
    })
    ElMessage.success(`Создана группа «${group.name}»`)
    visible.value = false
    emit('done')
  } catch {
    // axios interceptor handles toast
  } finally {
    creating.value = false
  }
}

function onEnter() {
  if (search.value.trim() && filteredGroups.value.length === 0) {
    createAndAdd()
  } else if (filteredGroups.value.length === 1) {
    addToGroup(filteredGroups.value[0].id, filteredGroups.value[0].name)
  }
}
</script>

<style scoped>
.atg-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.atg-search-row {
  display: flex;
  gap: 6px;
  align-items: center;
}

.atg-loading {
  display: flex;
  justify-content: center;
  padding: 12px 0;
  color: #909399;
}

.atg-empty {
  font-size: 13px;
  color: #909399;
  text-align: center;
  padding: 8px 0;
}

.atg-list {
  display: flex;
  flex-direction: column;
  max-height: 220px;
  overflow-y: auto;
}

.atg-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 7px 10px;
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.15s;
  gap: 8px;
}

.atg-item:hover {
  background: #f0f7ff;
}

.atg-item--loading {
  opacity: 0.5;
  pointer-events: none;
}

.atg-item-name {
  font-size: 13px;
  color: #303133;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.atg-item-count {
  font-size: 12px;
  color: #909399;
  flex-shrink: 0;
}
</style>
