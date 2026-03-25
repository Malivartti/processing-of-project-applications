<template>
  <el-dialog
    v-model="visible"
    title="Найти похожие проекты"
    width="480px"
    :close-on-click-modal="false"
    @closed="onClosed"
  >
    <div class="section-label">Пресет порога схожести</div>
    <el-button-group class="presets">
      <el-button
        v-for="preset in PRESETS"
        :key="preset.value"
        :type="thresholdPct === preset.value ? 'primary' : 'default'"
        size="small"
        @click="applyPreset(preset.value)"
      >
        {{ preset.label }}
      </el-button>
    </el-button-group>

    <div class="section-label" style="margin-top: 20px">Порог схожести: {{ thresholdPct }}</div>
    <el-slider
      v-model="thresholdPct"
      :min="0"
      :max="100"
      :step="1"
      :show-tooltip="false"
      style="padding: 0 8px"
    />

    <div class="manual-input-row">
      <span class="manual-input-label">Точное значение:</span>
      <el-input-number
        v-model="thresholdPct"
        :min="0"
        :max="100"
        :step="1"
        :precision="0"
        controls-position="right"
        size="small"
        style="width: 120px"
      />
    </div>

    <div class="hint">
      Строгий (70) — меньше групп, высокая точность.<br />
      Средний (50) — сбалансированный режим.<br />
      Мягкий (30) — больше групп, выше охват.
    </div>

    <template #footer>
      <el-button @click="visible = false">Отмена</el-button>
      <el-button type="primary" @click="onConfirm">Запустить</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

const PRESETS = [
  { label: 'Строгий (70)', value: 70 },
  { label: 'Средний (50)', value: 50 },
  { label: 'Мягкий (30)', value: 30 },
]

const LS_KEY = 'grouping_threshold_pct'

interface Props {
  modelValue: boolean
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  start: [threshold: number]
}>()

function loadThresholdPct(): number {
  const saved = localStorage.getItem(LS_KEY)
  if (saved !== null) {
    const parsed = parseInt(saved, 10)
    if (!isNaN(parsed) && parsed >= 0 && parsed <= 100) {
      return parsed
    }
  }
  return 50
}

const visible = ref(props.modelValue)
const thresholdPct = ref(loadThresholdPct())

watch(
  () => props.modelValue,
  (val) => {
    visible.value = val
  },
)

watch(visible, (val) => {
  emit('update:modelValue', val)
})

function applyPreset(value: number) {
  thresholdPct.value = value
}

function onConfirm() {
  localStorage.setItem(LS_KEY, String(thresholdPct.value))
  emit('start', thresholdPct.value / 100)
  visible.value = false
}

function onClosed() {
  // nothing to reset — threshold persists
}
</script>

<style scoped>
.section-label {
  font-size: 13px;
  color: #606266;
  margin-bottom: 8px;
  font-weight: 500;
}

.presets {
  display: flex;
  flex-wrap: wrap;
  gap: 0;
}

.manual-input-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 14px;
}

.manual-input-label {
  font-size: 13px;
  color: #606266;
}

.hint {
  margin-top: 16px;
  font-size: 12px;
  color: #909399;
  line-height: 1.7;
}
</style>
