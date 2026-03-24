<template>
  <el-drawer
    v-model="visible"
    direction="rtl"
    size="480px"
    :before-close="handleClose"
    @opened="drawerOpened = true"
    @closed="drawerOpened = false"
  >
    <template #header>
      <span class="drawer-title">{{ project?.title || "Загрузка..." }}</span>
    </template>

    <div v-if="loading || (!drawerOpened && !project)" class="loading-wrapper">
      <el-skeleton :rows="8" animated />
    </div>

    <div v-else-if="project" class="project-detail">
      <!-- Status tags -->
      <div class="status-tags">
        <el-tag v-if="project.is_selected" type="warning" size="small"
          >В отборе</el-tag
        >
        <el-tag v-else-if="project.is_auto_checked" type="success" size="small"
          >Проверен</el-tag
        >
        <el-tag v-else type="info" size="small">Новый</el-tag>
      </div>

      <!-- Meta fields -->
      <el-descriptions :column="1" border size="small" class="project-fields">
        <el-descriptions-item label="Направление">
          {{ project.direction?.name || "—" }}
        </el-descriptions-item>
        <el-descriptions-item label="Реализуется">
          {{ project.is_ongoing ? "Да" : "Нет" }}
        </el-descriptions-item>
        <el-descriptions-item label="Срок реализации">
          {{
            project.implementation_period
              ? `${project.implementation_period} сем.`
              : "—"
          }}
        </el-descriptions-item>
        <el-descriptions-item>
          <template #label>
            <el-tooltip
              content="Уровень готовности технологий"
              placement="top"
              effect="dark"
            >
              <span class="label-with-tip">
                УГТ
                <el-icon class="tip-icon"><QuestionFilled /></el-icon>
              </span>
            </el-tooltip>
          </template>
          {{
            project.trl_level
              ? `${project.trl_level.level} (${project.trl_level.name.split("—")[1]?.trim() ?? project.trl_level.name})`
              : "—"
          }}
        </el-descriptions-item>
      </el-descriptions>

      <!-- Text fields -->
      <div class="text-section">
        <div v-for="field in textFields" :key="field.label" class="text-field">
          <div class="field-label">{{ field.label }}</div>
          <div class="field-value" :class="{ 'field-empty': !field.value }">
            <template v-if="field.value">
              <HighlightedText
                :text="field.value"
                :keywords="props.searchKeywords ?? []"
              />
            </template>
            <template v-else>—</template>
          </div>
        </div>
      </div>

      <!-- Group info -->
      <div v-if="project.group" class="group-section">
        <div class="section-title">Группа</div>
        <div class="group-info">
          <div class="group-header">
            <el-tag
              :style="groupTagStyle(project.group)"
              size="default"
              effect="plain"
            >
              {{ project.group.name }}
            </el-tag>
            <el-tag size="small" type="info">
              {{ project.group.source === "auto" ? "Авто" : "Ручная" }}
            </el-tag>
            <el-tag
              v-if="project.group.is_confirmed"
              size="small"
              type="success"
            >
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
import { ref, watch, computed } from "vue";
import { ElMessage } from "element-plus";
import { QuestionFilled } from "@element-plus/icons-vue";
import { projectsApi, type ProjectRead, type GroupInfo } from "../api/projects";
import { groupsApi, type GroupRead } from "../api/groups";
import HighlightedText from "./HighlightedText.vue";

const props = defineProps<{
  projectId: string | null;
  searchKeywords?: string[];
}>();

const emit = defineEmits<{
  close: [];
  updated: [];
}>();

const visible = ref(false);
const drawerOpened = ref(false);
const loading = ref(false);
const actionLoading = ref(false);
const project = ref<ProjectRead | null>(null);
const groupDetail = ref<GroupRead | null>(null);

const projectCache = new Map<string, ProjectRead>();
const groupCache = new Map<string, GroupRead>();

const textFields = computed(() => {
  if (!project.value) return [];
  return [
    { label: "Актуальность", value: project.value.relevance },
    { label: "Проблема", value: project.value.problem },
    { label: "Цель", value: project.value.goal },
    { label: "Ключевые задачи", value: project.value.key_tasks },
    { label: "Ожидаемый результат", value: project.value.expected_result },
  ];
});

const groupProjects = computed(() => {
  if (!groupDetail.value || !project.value) return [];
  return groupDetail.value.projects.filter((p) => p.id !== project.value!.id);
});

watch(
  () => props.projectId,
  async (id) => {
    if (id) {
      visible.value = true;
      await loadProject(id);
    } else {
      visible.value = false;
    }
  },
);

async function loadProject(id: string) {
  if (projectCache.has(id)) {
    project.value = projectCache.get(id)!;
    const groupId = project.value.group?.id;
    groupDetail.value = groupId ? (groupCache.get(groupId) ?? null) : null;
    return;
  }
  loading.value = true;
  project.value = null;
  groupDetail.value = null;
  try {
    project.value = await projectsApi.getById(id);
    projectCache.set(id, project.value);
    if (project.value.group) {
      groupDetail.value = await groupsApi.getById(project.value.group.id);
      groupCache.set(project.value.group.id, groupDetail.value);
    }
  } catch {
    ElMessage.error("Не удалось загрузить проект");
  } finally {
    loading.value = false;
  }
}

function handleClose(done: () => void) {
  emit("close");
  done();
}

function groupTagStyle(group: GroupInfo) {
  return {
    border:
      group.source === "auto" ? "1px dashed #909399" : "1px solid #909399",
    color: "#606266",
  };
}

async function addToSelection() {
  if (!project.value) return;
  actionLoading.value = true;
  try {
    await projectsApi.select(project.value.id);
    project.value.is_selected = true;
    emit("updated");
  } finally {
    actionLoading.value = false;
  }
}

async function removeFromSelection() {
  if (!project.value) return;
  actionLoading.value = true;
  try {
    await projectsApi.deselect(project.value.id);
    project.value.is_selected = false;
    emit("updated");
  } finally {
    actionLoading.value = false;
  }
}

async function removeFromGroup() {
  if (!project.value?.group) return;
  actionLoading.value = true;
  try {
    await groupsApi.removeProject(project.value.group.id, project.value.id);
    project.value.group = null;
    groupDetail.value = null;
    emit("updated");
    ElMessage.success("Проект убран из группы");
  } finally {
    actionLoading.value = false;
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

.field-empty {
  color: #c0c4cc;
}

.label-with-tip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.tip-icon {
  font-size: 13px;
  color: #c0c4cc;
  cursor: help;
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
