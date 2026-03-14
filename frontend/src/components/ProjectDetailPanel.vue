<template>
  <el-drawer
    v-model="visible"
    direction="rtl"
    size="480px"
    :before-close="handleClose"
  >
    <template #header>
      <span class="drawer-title">{{ project?.title || 'Загрузка...' }}</span>
    </template>

    <div v-if="loading" class="loading-wrapper">
      <el-skeleton :rows="8" animated />
    </div>

    <div v-else-if="project" class="project-detail">
      <!-- Status tags -->
      <div class="status-tags">
        <el-tag :type="project.is_ongoing ? 'info' : 'success'" size="small">
          {{ project.is_ongoing ? 'Бессрочный' : 'Срочный' }}
        </el-tag>
        <el-tag v-if="project.is_selected" type="warning" size="small">В отборе</el-tag>
        <el-tag v-else-if="project.is_auto_checked" type="success" size="small">Проверен</el-tag>
        <el-tag v-else type="info" size="small">Новый</el-tag>
      </div>

      <!-- Dictionary fields -->
      <el-descriptions :column="1" border size="small" class="project-fields">
        <el-descriptions-item label="Направление">
          {{ project.direction_name || '—' }}
        </el-descriptions-item>
        <el-descriptions-item label="Приор. направление">
          {{ project.priority_direction_name || '—' }}
        </el-descriptions-item>
        <el-descriptions-item label="УГТ">
          {{ project.trl_name || '—' }}
        </el-descriptions-item>
      </el-descriptions>

      <!-- Text fields -->
      <div class="text-section">
        <div v-if="project.problem" class="text-field">
          <div class="field-label">Проблема</div>
          <div class="field-value">{{ project.problem }}</div>
        </div>
        <div v-if="project.goal" class="text-field">
          <div class="field-label">Цель</div>
          <div class="field-value">{{ project.goal }}</div>
        </div>
        <div v-if="project.expected_result" class="text-field">
          <div class="field-label">Ожидаемый результат</div>
          <div class="field-value">{{ project.expected_result }}</div>
        </div>
      </div>

      <!-- Group info -->
      <div v-if="project.group" class="group-section">
        <div class="section-title">Группа</div>
        <div class="group-info">
          <div class="group-header">
            <el-tag :style="groupTagStyle(project.group)" size="default" effect="plain">
              {{ project.group.name }}
            </el-tag>
            <el-tag size="small" type="info">
              {{ project.group.source === 'auto' ? 'Авто' : 'Ручная' }}
            </el-tag>
            <el-tag v-if="project.group.is_confirmed" size="small" type="success">
              Подтверждена
            </el-tag>
          </div>
          <div v-if="groupProjects.length" class="group-projects">
            <div class="group-projects-label">Другие проекты в группе:</div>
            <ul class="group-projects-list">
              <li v-for="p in groupProjects" :key="p.id">{{ p.title }}</li>
            </ul>
          </div>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="drawer-actions">
        <el-button
          v-if="project?.group"
          type="danger"
          plain
          size="small"
          :loading="actionLoading"
          @click="removeFromGroup"
        >
          Убрать из группы
        </el-button>
        <div class="spacer" />
        <el-button
          v-if="!project?.is_selected"
          type="primary"
          size="small"
          :loading="actionLoading"
          @click="addToSelection"
        >
          Добавить в отбор
        </el-button>
        <el-button
          v-else
          type="warning"
          plain
          size="small"
          :loading="actionLoading"
          @click="removeFromSelection"
        >
          Убрать из отбора
        </el-button>
      </div>
    </template>
  </el-drawer>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { projectsApi, type ProjectRead, type GroupInfo } from '../api/projects'
import { groupsApi, type GroupRead } from '../api/groups'

const props = defineProps<{
  projectId: string | null
}>()

const emit = defineEmits<{
  close: []
  updated: []
}>()

const visible = ref(false)
const loading = ref(false)
const actionLoading = ref(false)
const project = ref<ProjectRead | null>(null)
const groupDetail = ref<GroupRead | null>(null)

const groupProjects = computed(() => {
  if (!groupDetail.value || !project.value) return []
  return groupDetail.value.projects.filter((p) => p.id !== project.value!.id)
})

watch(
  () => props.projectId,
  async (id) => {
    if (id) {
      visible.value = true
      await loadProject(id)
    } else {
      visible.value = false
    }
  },
)

async function loadProject(id: string) {
  loading.value = true
  project.value = null
  groupDetail.value = null
  try {
    project.value = await projectsApi.getById(id)
    if (project.value.group) {
      groupDetail.value = await groupsApi.getById(project.value.group.id)
    }
  } catch {
    ElMessage.error('Не удалось загрузить проект')
  } finally {
    loading.value = false
  }
}

function handleClose(done: () => void) {
  emit('close')
  done()
}

function groupTagStyle(group: GroupInfo) {
  return {
    border: group.source === 'auto' ? '1px dashed #909399' : '1px solid #909399',
    color: '#606266',
  }
}

async function addToSelection() {
  if (!project.value) return
  actionLoading.value = true
  try {
    await projectsApi.select(project.value.id)
    project.value.is_selected = true
    emit('updated')
  } finally {
    actionLoading.value = false
  }
}

async function removeFromSelection() {
  if (!project.value) return
  actionLoading.value = true
  try {
    await projectsApi.deselect(project.value.id)
    project.value.is_selected = false
    emit('updated')
  } finally {
    actionLoading.value = false
  }
}

async function removeFromGroup() {
  if (!project.value?.group) return
  actionLoading.value = true
  try {
    await groupsApi.removeProject(project.value.group.id, project.value.id)
    project.value.group = null
    groupDetail.value = null
    emit('updated')
    ElMessage.success('Проект убран из группы')
  } finally {
    actionLoading.value = false
  }
}
</script>

<style scoped>
.drawer-title {
  font-size: 15px;
  font-weight: 600;
  line-height: 1.4;
}

.loading-wrapper {
  padding: 8px 0;
}

.project-detail {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.status-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.project-fields {
  margin-top: 4px;
}

.text-section {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.text-field {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.field-label {
  font-size: 12px;
  color: #909399;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.field-value {
  font-size: 14px;
  color: #303133;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}

.section-title {
  font-size: 13px;
  font-weight: 600;
  color: #606266;
  margin-bottom: 8px;
}

.group-info {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.group-header {
  display: flex;
  gap: 6px;
  align-items: center;
  flex-wrap: wrap;
}

.group-projects-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}

.group-projects-list {
  margin: 0;
  padding-left: 18px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.group-projects-list li {
  font-size: 13px;
  color: #606266;
  line-height: 1.4;
}

.drawer-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.spacer {
  flex: 1;
}
</style>
