<template>
  <div class="grouping-progress">
    <div class="progress-header">
      <span class="stage-label">{{ stageLabel }}</span>
      <span class="progress-text">{{ props.current }} / {{ props.total }}</span>
    </div>
    <el-progress
      :percentage="percentage"
      :status="progressStatus"
      :striped="isRunning"
      :striped-flow="isRunning"
      :duration="10"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onUnmounted, ref, watch } from 'vue'
import { groupingApi } from '../api/grouping'

interface Props {
  runId: string
  context: string
}

const props = defineProps<Props>()
const emit = defineEmits<{
  completed: [groupsFound: number]
  error: [message: string]
}>()

const STAGE_LABELS: Record<string, string> = {
  embeddings: 'Вычисление эмбеддингов',
  similarity: 'Расчёт схожести',
  clustering: 'Кластеризация',
  saving: 'Сохранение',
  done: 'Завершено',
}

const stage = ref('')
const current = ref(0)
const total = ref(0)
const status = ref('')

const stageLabel = computed(() => STAGE_LABELS[stage.value] || stage.value || 'Запуск...')

const percentage = computed(() => {
  if (total.value === 0) return 0
  return Math.min(100, Math.round((current.value / total.value) * 100))
})

const isRunning = computed(() => stage.value !== 'done' && status.value !== 'failed')

const progressStatus = computed(() => {
  if (status.value === 'failed') return 'exception'
  if (stage.value === 'done') return 'success'
  return ''
})

let intervalId: ReturnType<typeof setInterval> | null = null

async function poll() {
  try {
    const res = await groupingApi.getGroupingStatus(props.runId)
    stage.value = res.stage
    current.value = res.current
    total.value = res.total
    status.value = res.status

    if (res.stage === 'done') {
      stopPolling()
      emit('completed', res.groups_found ?? 0)
    } else if (res.status === 'failed') {
      stopPolling()
      emit('error', res.error ?? 'Ошибка группировки')
    }
  } catch {
    // axios interceptor shows error toast; stop polling to avoid spam
    stopPolling()
    emit('error', 'Ошибка при получении статуса группировки')
  }
}

function startPolling() {
  poll()
  intervalId = setInterval(poll, 2000)
}

function stopPolling() {
  if (intervalId !== null) {
    clearInterval(intervalId)
    intervalId = null
  }
}

watch(
  () => props.runId,
  (id) => {
    if (id) {
      stopPolling()
      stage.value = ''
      current.value = 0
      total.value = 0
      status.value = ''
      startPolling()
    }
  },
  { immediate: true },
)

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped>
.grouping-progress {
  padding: 8px 0;
  min-width: 260px;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.stage-label {
  font-size: 13px;
  color: #303133;
  font-weight: 500;
}

.progress-text {
  font-size: 12px;
  color: #909399;
}
</style>
