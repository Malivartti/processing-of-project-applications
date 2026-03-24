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
          <el-tag
            v-if="result.score !== null"
            :type="scoreType"
            size="large"
            effect="dark"
            class="score-tag"
          >
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
              >{{ kw }}</el-tag
            >
          </div>
        </div>
      </div>

      <!-- Highlight controls -->
      <div class="highlight-controls">
        <el-checkbox v-model="showKeywords">Подсветка ключевых слов</el-checkbox>
        <el-checkbox v-model="showSubstrings">Подсветка общих подстрок</el-checkbox>
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
              <td class="td-value">{{ meta.a ?? "—" }}</td>
              <td class="td-value">{{ meta.b ?? "—" }}</td>
            </tr>
            <!-- Divider row -->
            <tr class="tr-divider">
              <td colspan="3"></td>
            </tr>
            <!-- Text field rows -->
            <tr v-for="field in fieldRows" :key="field.key" class="tr-field">
              <td class="td-section">{{ field.label }}</td>
              <td class="td-value td-text">
                <HighlightedText
                  :text="field.a"
                  :keywords="showKeywords ? result.highlight_tokens : []"
                  :substrings="fieldSubstrings[field.key]"
                />
              </td>
              <td class="td-value td-text">
                <HighlightedText
                  :text="field.b"
                  :keywords="showKeywords ? result.highlight_tokens : []"
                  :substrings="fieldSubstrings[field.key]"
                />
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
import { ref, watch, computed } from "vue";

const MIN_SUBSTRING_LEN = 10

function findCommonSubstrings(textA: string, textB: string): string[] {
  if (!textA || !textB) return []
  const a = textA.toLowerCase()
  const b = textB.toLowerCase()
  const m = a.length
  const n = b.length

  const found = new Set<string>()
  let prev = new Array<number>(n + 1).fill(0)
  let curr = new Array<number>(n + 1).fill(0)

  for (let i = 1; i <= m; i++) {
    for (let j = 1; j <= n; j++) {
      if (a[i - 1] === b[j - 1]) {
        curr[j] = prev[j - 1] + 1
        if (curr[j] >= MIN_SUBSTRING_LEN) {
          found.add(textA.slice(i - curr[j], i))
        }
      } else {
        curr[j] = 0
      }
    }
    ;[prev, curr] = [curr, new Array<number>(n + 1).fill(0)]
  }

  // Keep only maximal substrings (remove those contained in a longer one)
  const arr = Array.from(found)
  return arr.filter(
    (s) => !arr.some((longer) => longer.length > s.length && longer.toLowerCase().includes(s.toLowerCase())),
  )
}
import { projectsApi, type CompareResponse } from "../api/projects";
import HighlightedText from "./HighlightedText.vue";

const props = defineProps<{
  modelValue: boolean;
  projectIds: [string, string] | null;
}>();

const emit = defineEmits<{
  "update:modelValue": [value: boolean];
}>();

const loading = ref(false);
const result = ref<CompareResponse | null>(null);
const showKeywords = ref(true);
const showSubstrings = ref(false);

const visible = computed({
  get: () => props.modelValue,
  set: (v) => emit("update:modelValue", v),
});

const scoreType = computed(() => {
  if (!result.value?.score) return "info";
  if (result.value.score >= 0.8) return "danger";
  if (result.value.score >= 0.6) return "warning";
  return "success";
});

const metaRows = computed(() => {
  if (!result.value) return [];
  const a = result.value.project_a;
  const b = result.value.project_b;
  const trlLabel = (p: typeof a) =>
    p.trl_level
      ? `${p.trl_level.level} (${p.trl_level.name.split("—")[1]?.trim() ?? p.trl_level.name})`
      : null;
  const periodLabel = (p: typeof a) =>
    p.implementation_period ? `${p.implementation_period} сем.` : null;
  return [
    {
      key: "direction",
      label: "Направление",
      a: a.direction?.name,
      b: b.direction?.name,
    },
    { key: "trl", label: "УГТ", a: trlLabel(a), b: trlLabel(b) },
    { key: "period", label: "Срок", a: periodLabel(a), b: periodLabel(b) },
    {
      key: "ongoing",
      label: "Реализуется",
      a: a.is_ongoing ? "Да" : "Нет",
      b: b.is_ongoing ? "Да" : "Нет",
    },
  ];
});

const fieldRows = computed(() => {
  if (!result.value) return [];
  const a = result.value.project_a;
  const b = result.value.project_b;
  return [
    { key: "relevance", label: "Актуальность", a: a.relevance, b: b.relevance },
    { key: "problem", label: "Проблема", a: a.problem, b: b.problem },
    { key: "goal", label: "Цель", a: a.goal, b: b.goal },
    {
      key: "key_tasks",
      label: "Ключевые задачи",
      a: a.key_tasks,
      b: b.key_tasks,
    },
    {
      key: "result",
      label: "Ожидаемый результат",
      a: a.expected_result,
      b: b.expected_result,
    },
  ];
});

const fieldSubstrings = computed((): Record<string, string[]> => {
  if (!showSubstrings.value || !result.value) return {};
  const res: Record<string, string[]> = {};
  for (const field of fieldRows.value) {
    res[field.key] = findCommonSubstrings(field.a ?? "", field.b ?? "");
  }
  return res;
});

async function fetchCompare(ids: [string, string]) {
  loading.value = true;
  result.value = null;
  try {
    result.value = await projectsApi.compare(ids[0], ids[1]);
  } finally {
    loading.value = false;
  }
}

watch(
  () => props.projectIds,
  (ids) => {
    if (ids && props.modelValue) fetchCompare(ids);
  },
);

watch(
  () => props.modelValue,
  (open) => {
    if (open && props.projectIds && !result.value)
      fetchCompare(props.projectIds);
  },
);

function onClosed() {
  result.value = null;
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

/* ── Highlight controls ───────────────────────────── */
.highlight-controls {
  display: flex;
  gap: 24px;
  padding: 8px 4px;
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
