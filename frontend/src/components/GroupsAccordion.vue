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
          <div class="group-header">
            <el-tag
              :color="getGroupColor(group.id)"
              :style="groupTagStyle(group)"
              size="small"
              effect="plain"
              class="group-name-tag"
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
import { ref, computed } from 'vue'
import type { ProjectListItem } from '../api/projects'
import type { GroupListItem } from '../api/groups'

const props = defineProps<{
  items: ProjectListItem[]
  groups: GroupListItem[]
  loading: boolean
}>()

defineEmits<{
  (e: 'project-click', id: string): void
}>()

const openGroups = ref<string[]>([])
const openUngrouped = ref<string[]>(['ungrouped'])

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

function groupTagStyle(group: GroupListItem) {
  return {
    border: !group.is_confirmed && group.source === 'auto'
      ? '1px dashed #909399'
      : '1px solid #909399',
    color: '#606266',
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
  const groupMap = new Map<string, { id: string; name: string; source: string; is_confirmed: boolean; projects: ProjectListItem[] }>()

  for (const item of props.items) {
    if (!item.group_id || !item.group_name) continue

    if (!groupMap.has(item.group_id)) {
      const meta = groupMetaById.value.get(item.group_id)
      groupMap.set(item.group_id, {
        id: item.group_id,
        name: item.group_name,
        source: item.group_source ?? 'manual',
        is_confirmed: meta?.is_confirmed ?? false,
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
}

.group-name-tag {
  font-weight: 500;
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
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
