<template>
  <div class="history-view">
    <div class="history-header">
      <h2>История группировок</h2>
      <el-button :icon="Refresh" :loading="loading" @click="load">Обновить</el-button>
    </div>

    <el-table
      v-loading="loading"
      :data="items"
      stripe
      style="width: 100%"
      empty-text="Нет запусков группировки"
    >
      <el-table-column label="Дата и время" min-width="160">
        <template #default="{ row }">
          {{ formatDate(row.started_at) }}
        </template>
      </el-table-column>

      <el-table-column label="Контекст" width="120">
        <template #default="{ row }">
          <el-tag :type="row.context === 'main' ? 'primary' : 'warning'" size="small">
            {{ row.context === 'main' ? 'Основной' : 'Отбор' }}
          </el-tag>
        </template>
      </el-table-column>

      <el-table-column label="Порог" width="90" align="center">
        <template #default="{ row }">
          {{ Math.round(row.threshold * 100) }}
        </template>
      </el-table-column>

      <el-table-column label="Обработано" width="120" align="center">
        <template #default="{ row }">
          {{ row.projects_processed ?? '—' }}
        </template>
      </el-table-column>

      <el-table-column label="Групп найдено" width="130" align="center">
        <template #default="{ row }">
          {{ row.groups_found ?? '—' }}
        </template>
      </el-table-column>

      <el-table-column label="В группах" width="110" align="center">
        <template #default="{ row }">
          {{ row.projects_in_groups ?? '—' }}
        </template>
      </el-table-column>

      <el-table-column label="Подтверждено" width="130" align="center">
        <template #default="{ row }">
          <span v-if="row.confirmed_rate !== null">
            {{ (row.confirmed_rate * 100).toFixed(0) }}%
          </span>
          <span v-else>—</span>
        </template>
      </el-table-column>

      <el-table-column label="Статус" width="130">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)" size="small">
            {{ statusLabel(row.status) }}
          </el-tag>
          <el-tooltip v-if="row.error_message" :content="row.error_message" placement="top">
            <el-icon class="error-icon"><Warning /></el-icon>
          </el-tooltip>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Refresh, Warning } from '@element-plus/icons-vue'
import { groupingApi, type GroupingRunRead } from '@/api/grouping'

const items = ref<GroupingRunRead[]>([])
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    const resp = await groupingApi.getGroupingHistory()
    items.value = resp.items
  } finally {
    loading.value = false
  }
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function statusLabel(status: string): string {
  const map: Record<string, string> = {
    pending: 'Ожидание',
    running: 'Выполняется',
    completed: 'Завершено',
    failed: 'Ошибка',
  }
  return map[status] ?? status
}

function statusType(status: string): '' | 'success' | 'warning' | 'danger' | 'info' {
  const map: Record<string, '' | 'success' | 'warning' | 'danger' | 'info'> = {
    pending: 'info',
    running: 'warning',
    completed: 'success',
    failed: 'danger',
  }
  return map[status] ?? ''
}

onMounted(load)
</script>

<style scoped>
.history-view {
  padding: 16px;
}
.history-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}
.history-header h2 {
  margin: 0;
}
.error-icon {
  color: var(--el-color-danger);
  margin-left: 4px;
  vertical-align: middle;
  cursor: pointer;
}
</style>
