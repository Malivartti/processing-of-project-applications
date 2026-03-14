<template>
  <el-dialog
    v-model="visible"
    title="Создать группу"
    width="480px"
    :close-on-click-modal="false"
    @closed="onClosed"
  >
    <div class="selected-info">
      <span>Выбрано проектов: <strong>{{ projectIds.length }}</strong></span>
    </div>

    <!-- Conflict warning -->
    <el-alert
      v-if="conflicting.length"
      type="warning"
      :closable="false"
      style="margin-bottom: 16px"
    >
      <template #title>
        Следующие проекты уже состоят в группах:
      </template>
      <ul class="conflict-list">
        <li v-for="c in conflicting" :key="c.project_id">
          <strong>{{ getProjectTitle(c.project_id) }}</strong> — группа «{{ c.group_name }}»
        </li>
      </ul>
      <div style="margin-top: 8px">Пожалуйста, уберите их из выбора или измените группировку.</div>
    </el-alert>

    <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
      <el-form-item label="Название группы" prop="name">
        <el-input v-model="form.name" placeholder="Введите название" maxlength="200" show-word-limit />
      </el-form-item>
      <el-form-item label="Описание" prop="description">
        <el-input
          v-model="form.description"
          type="textarea"
          :rows="3"
          placeholder="Необязательно"
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="visible = false">Отмена</el-button>
      <el-button type="primary" :loading="loading" @click="onSubmit">Создать</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage } from 'element-plus'
import { groupsApi, type ConflictingProject } from '../api/groups'
import type { ProjectListItem } from '../api/projects'

interface Props {
  modelValue: boolean
  selectedProjects: ProjectListItem[]
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  created: []
}>()

const visible = ref(props.modelValue)
const loading = ref(false)
const conflicting = ref<ConflictingProject[]>([])

const projectIds = ref<string[]>([])

watch(
  () => props.modelValue,
  (val) => {
    visible.value = val
    if (val) {
      projectIds.value = props.selectedProjects.map((p) => p.id)
      conflicting.value = []
      form.name = ''
      form.description = ''
    }
  },
)

watch(visible, (val) => {
  emit('update:modelValue', val)
})

const formRef = ref<FormInstance>()
const form = reactive({ name: '', description: '' })
const rules: FormRules = {
  name: [{ required: true, message: 'Введите название', trigger: 'blur' }],
}

function getProjectTitle(projectId: string): string {
  const p = props.selectedProjects.find((x) => x.id === projectId)
  return p?.title ?? projectId
}

async function onSubmit() {
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  conflicting.value = []
  try {
    await groupsApi.create({
      name: form.name,
      description: form.description || null,
      project_ids: projectIds.value,
      context: 'main',
    })
    ElMessage.success('Группа создана')
    visible.value = false
    emit('created')
  } catch (err: unknown) {
    const e = err as { response?: { status?: number; data?: { detail?: { conflicting?: ConflictingProject[] } } } }
    if (e?.response?.status === 409) {
      conflicting.value = e.response.data?.detail?.conflicting ?? []
    }
    // axios interceptor handles the toast for other errors
  } finally {
    loading.value = false
  }
}

function onClosed() {
  conflicting.value = []
  form.name = ''
  form.description = ''
}
</script>

<style scoped>
.selected-info {
  margin-bottom: 16px;
  color: #606266;
  font-size: 14px;
}

.conflict-list {
  margin: 8px 0 0 16px;
  padding: 0;
}

.conflict-list li {
  margin-bottom: 4px;
}
</style>
