<template>
  <el-dialog
    v-model="visible"
    title="Сравнение проектов"
    width="90%"
    :max-width="1200"
    top="5vh"
    align-center
    destroy-on-close
    @closed="onClosed"
  >
    <div v-if="loading" class="compare-loading">
      <el-skeleton :rows="6" animated />
    </div>

    <div v-else-if="result" class="compare-body">
      <!-- Score row -->
      <div class="score-row">
        <div class="project-col-header">{{ result.project_a.title }}</div>
        <div class="score-center">
          <el-tag v-if="result.score !== null" :type="scoreType" size="large" effect="dark">
            Сходство: {{ (result.score * 100).toFixed(1) }}%
          </el-tag>
          <el-tag v-else type="info" size="large">Сходство: н/д</el-tag>
          <div v-if="result.keywords.length" class="keywords-label">
            Ключевые слова: {{ result.keywords.join(', ') }}
          </div>
        </div>
        <div class="project-col-header">{{ result.project_b.title }}</div>
      </div>

      <el-divider />

      <!-- Side-by-side fields -->
      <div class="compare-cols">
        <div class="project-col">
          <ProjectFields :project="result.project_a" :keywords="result.keywords" />
        </div>
        <div class="divider-v" />
        <div class="project-col">
          <ProjectFields :project="result.project_b" :keywords="result.keywords" />
        </div>
      </div>
    </div>

    <template #footer>
      <el-button @click="visible = false">Закрыть</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { projectsApi, type CompareResponse, type ProjectRead } from '../api/projects'
import HighlightedText from './HighlightedText.vue'

// Sub-component for project fields (defined inline to keep file self-contained)
import { defineComponent, h } from 'vue'

const ProjectFields = defineComponent({
  props: {
    project: { type: Object as () => ProjectRead, required: true },
    keywords: { type: Array as () => string[], default: () => [] },
  },
  setup(props) {
    const fields = computed(() => [
      { label: 'Описание проблемы', value: props.project.problem },
      { label: 'Цель', value: props.project.goal },
      { label: 'Ожидаемый результат', value: props.project.expected_result },
    ])
    return { fields }
  },
  render() {
    return h('div', { class: 'project-fields' }, [
      h('div', { class: 'field-meta' }, [
        h('span', { class: 'meta-item' }, `Направление: ${this.project.direction_name ?? '—'}`),
        h('span', { class: 'meta-item' }, `Приор. направление: ${this.project.priority_direction_name ?? '—'}`),
        h('span', { class: 'meta-item' }, `УГТ: ${this.project.trl_name ?? '—'}`),
        h('span', { class: 'meta-item' }, `Срок: ${this.project.is_ongoing ? 'Бессрочный' : 'Срочный'}`),
      ]),
      ...this.fields.map((f) =>
        h('div', { class: 'field-block' }, [
          h('div', { class: 'field-label' }, f.label),
          h('div', { class: 'field-value' }, [
            h(HighlightedText, { text: f.value, keywords: this.keywords }),
          ]),
        ]),
      ),
    ])
  },
})

const props = defineProps<{
  modelValue: boolean
  projectIds: [string, string] | null
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

const loading = ref(false)
const result = ref<CompareResponse | null>(null)

const visible = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v),
})

const scoreType = computed(() => {
  if (!result.value?.score) return 'info'
  if (result.value.score >= 0.8) return 'danger'
  if (result.value.score >= 0.6) return 'warning'
  return 'success'
})

watch(
  () => props.projectIds,
  async (ids) => {
    if (!ids || !props.modelValue) return
    loading.value = true
    result.value = null
    try {
      result.value = await projectsApi.compare(ids[0], ids[1])
    } finally {
      loading.value = false
    }
  },
)

watch(
  () => props.modelValue,
  async (open) => {
    if (open && props.projectIds && !result.value) {
      loading.value = true
      try {
        result.value = await projectsApi.compare(props.projectIds[0], props.projectIds[1])
      } finally {
        loading.value = false
      }
    }
  },
)

function onClosed() {
  result.value = null
}
</script>

<style scoped>
.compare-loading {
  padding: 16px;
}

.compare-body {
  padding: 0 4px;
}

.score-row {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  align-items: center;
  gap: 16px;
  margin-bottom: 8px;
}

.project-col-header {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  line-height: 1.4;
}

.score-center {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  min-width: 180px;
}

.keywords-label {
  font-size: 12px;
  color: #909399;
  text-align: center;
  max-width: 200px;
  word-break: break-word;
}

.compare-cols {
  display: grid;
  grid-template-columns: 1fr 1px 1fr;
  gap: 20px;
  max-height: 65vh;
  overflow-y: auto;
}

.divider-v {
  background: #e4e7ed;
  width: 1px;
  align-self: stretch;
}

.project-col {
  padding: 0 4px;
}

/* ProjectFields styles (non-scoped inner component, use :deep or global) */
:deep(.project-fields) {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

:deep(.field-meta) {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 8px 12px;
  background: #f8f9fa;
  border-radius: 6px;
  margin-bottom: 4px;
}

:deep(.meta-item) {
  font-size: 12px;
  color: #606266;
}

:deep(.field-block) {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

:deep(.field-label) {
  font-size: 12px;
  font-weight: 600;
  color: #909399;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

:deep(.field-value) {
  font-size: 14px;
  color: #303133;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}
</style>
