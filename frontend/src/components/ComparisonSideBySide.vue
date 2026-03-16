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
      <!-- Similarity + keywords block -->
      <div class="meta-block">
        <div class="score-area">
          <span class="score-label">Семантическое сходство</span>
          <el-tag v-if="result.score !== null" :type="scoreType" size="large" effect="dark" class="score-tag">
            {{ (result.score * 100).toFixed(1) }}%
          </el-tag>
          <el-tag v-else type="info" size="large" effect="plain">н/д</el-tag>
        </div>
        <div v-if="result.keywords.length" class="keywords-area">
          <span class="keywords-title">Общие ключевые слова</span>
          <div class="keywords-tags">
            <el-tag
              v-for="kw in result.keywords"
              :key="kw"
              type="warning"
              effect="light"
              size="small"
              class="kw-tag"
            >{{ kw }}</el-tag>
          </div>
        </div>
      </div>

      <!-- Comparison table -->
      <div class="compare-table-wrap">
        <table class="compare-table">
          <colgroup>
            <col class="col-section" />
            <col class="col-project" />
            <col class="col-project" />
          </colgroup>
          <thead>
            <tr>
              <th class="th-section"></th>
              <th class="th-project">{{ result.project_a.title }}</th>
              <th class="th-project">{{ result.project_b.title }}</th>
            </tr>
          </thead>
          <tbody>
            <!-- Meta rows -->
            <tr v-for="meta in metaRows" :key="meta.key" class="tr-meta">
              <td class="td-section">{{ meta.label }}</td>
              <td class="td-value">{{ meta.a ?? '—' }}</td>
              <td class="td-value">{{ meta.b ?? '—' }}</td>
            </tr>
            <!-- Divider row -->
            <tr class="tr-divider">
              <td colspan="3"></td>
            </tr>
            <!-- Text field rows -->
            <tr v-for="field in fieldRows" :key="field.key" class="tr-field">
              <td class="td-section">{{ field.label }}</td>
              <td class="td-value td-text">
                <HighlightedText :text="field.a" :keywords="result.keywords" />
              </td>
              <td class="td-value td-text">
                <HighlightedText :text="field.b" :keywords="result.keywords" />
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <template #footer>
      <el-button @click="visible = false">Закрыть</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { projectsApi, type CompareResponse } from '../api/projects'
import HighlightedText from './HighlightedText.vue'

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

const metaRows = computed(() => {
  if (!result.value) return []
  const a = result.value.project_a
  const b = result.value.project_b
  return [
    { key: 'direction', label: 'Направление', a: a.direction_name, b: b.direction_name },
    { key: 'priority', label: 'Приор. направление', a: a.priority_direction_name, b: b.priority_direction_name },
    { key: 'trl', label: 'УГТ', a: a.trl_name, b: b.trl_name },
    { key: 'ongoing', label: 'Срок', a: a.is_ongoing ? 'Бессрочный' : 'Срочный', b: b.is_ongoing ? 'Бессрочный' : 'Срочный' },
  ]
})

const fieldRows = computed(() => {
  if (!result.value) return []
  const a = result.value.project_a
  const b = result.value.project_b
  return [
    { key: 'problem', label: 'Описание проблемы', a: a.problem, b: b.problem },
    { key: 'goal', label: 'Цель', a: a.goal, b: b.goal },
    { key: 'result', label: 'Ожидаемый результат', a: a.expected_result, b: b.expected_result },
  ]
})

async function fetchCompare(ids: [string, string]) {
  loading.value = true
  result.value = null
  try {
    result.value = await projectsApi.compare(ids[0], ids[1])
  } finally {
    loading.value = false
  }
}

watch(
  () => props.projectIds,
  (ids) => { if (ids && props.modelValue) fetchCompare(ids) },
)

watch(
  () => props.modelValue,
  (open) => { if (open && props.projectIds && !result.value) fetchCompare(props.projectIds) },
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
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* ── Meta block ───────────────────────────────────── */
.meta-block {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 32px;
  padding: 16px 24px;
  background: #f5f7fa;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
  flex-wrap: wrap;
}

.score-area {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

.score-label {
  font-size: 15px;
  color: #606266;
  font-weight: 500;
}

.score-tag {
  font-size: 18px;
  padding: 0 16px;
  height: 36px;
  line-height: 36px;
}

.keywords-area {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  flex-wrap: wrap;
}

.keywords-title {
  font-size: 15px;
  color: #606266;
  font-weight: 500;
  white-space: nowrap;
  padding-top: 3px;
}

.keywords-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.kw-tag {
  font-size: 13px;
}

/* ── Compare table ────────────────────────────────── */
.compare-table-wrap {
  max-height: 62vh;
  overflow-y: auto;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
}

.compare-table {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
}

.col-section {
  width: 148px;
}

.col-project {
  width: calc((100% - 148px) / 2);
}

thead tr {
  background: #f5f7fa;
  position: sticky;
  top: 0;
  z-index: 1;
}

.th-section {
  width: 148px;
  padding: 10px 12px;
  border-bottom: 2px solid #dcdfe6;
  text-align: left;
}

.th-project {
  padding: 10px 14px;
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  border-bottom: 2px solid #dcdfe6;
  border-left: 1px solid #e4e7ed;
  line-height: 1.4;
  word-break: break-word;
}

.tr-meta .td-section,
.tr-meta .td-value {
  padding: 8px 12px;
  font-size: 13px;
  border-bottom: 1px solid #f0f2f5;
  vertical-align: top;
}

.tr-meta .td-value {
  color: #606266;
}

.tr-divider td {
  height: 6px;
  background: #f0f2f5;
  border-top: 1px solid #e4e7ed;
  border-bottom: 1px solid #e4e7ed;
}

.tr-field .td-section,
.tr-field .td-value {
  padding: 12px 14px;
  border-bottom: 1px solid #ebeef5;
  vertical-align: top;
}

.td-section {
  font-size: 12px;
  font-weight: 600;
  color: #909399;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  background: #fafafa;
  border-right: 1px solid #e4e7ed;
  white-space: normal;
  word-break: break-word;
}

.td-value {
  font-size: 13px;
  color: #303133;
  border-left: 1px solid #e4e7ed;
}

.td-text {
  font-size: 14px;
  line-height: 1.65;
  white-space: pre-wrap;
  word-break: break-word;
}

.tr-field:last-child .td-section,
.tr-field:last-child .td-value {
  border-bottom: none;
}
</style>
