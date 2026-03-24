<template>
  <div class="dictionary-editor">
    <el-table :data="items" style="width: 100%" v-loading="loading">
      <el-table-column label="Название" min-width="200">
        <template #default="{ row }">
          <template v-if="editingId === row.id">
            <el-input v-model="editName" size="small" style="width: 200px" />
          </template>
          <span v-else :class="{ 'text-inactive': !row.is_active }">
            {{ row.name }}
            <el-icon v-if="!row.is_active" class="icon-inactive" title="Неактивно">
              <component :is="RemoveFilled" />
            </el-icon>
          </span>
        </template>
      </el-table-column>

      <el-table-column v-if="showLevel" label="Уровень" width="120">
        <template #default="{ row }">
          <template v-if="editingId === row.id">
            <el-input-number v-model="editLevel" :min="1" :max="9" size="small" style="width: 90px" />
          </template>
          <span v-else :class="{ 'text-inactive': !row.is_active }">{{ row.level ?? '—' }}</span>
        </template>
      </el-table-column>

      <el-table-column label="Статус" width="120">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
            {{ row.is_active ? 'Активно' : 'Неактивно' }}
          </el-tag>
        </template>
      </el-table-column>

      <el-table-column label="Действия" width="160" align="right">
        <template #default="{ row }">
          <template v-if="editingId === row.id">
            <el-button size="small" type="primary" :loading="saving" @click="saveEdit(row)">Сохранить</el-button>
            <el-button size="small" @click="cancelEdit">Отмена</el-button>
          </template>
          <template v-else>
            <el-button
              v-if="row.is_active"
              size="small"
              :icon="Edit"
              @click="startEdit(row)"
              title="Редактировать"
            />
            <el-button
              v-if="row.is_active"
              size="small"
              type="danger"
              :icon="Delete"
              @click="handleDeactivate(row)"
              title="Деактивировать"
            />
          </template>
        </template>
      </el-table-column>
    </el-table>

    <div class="add-row">
      <el-input
        v-model="newName"
        placeholder="Новое значение..."
        size="small"
        style="width: 200px"
        @keyup.enter="handleAdd"
      />
      <el-input-number
        v-if="showLevel"
        v-model="newLevel"
        :min="1"
        :max="9"
        size="small"
        placeholder="УГТ"
        style="width: 90px; margin-left: 8px"
      />
      <el-button
        size="small"
        type="primary"
        :disabled="!newName.trim()"
        :loading="adding"
        @click="handleAdd"
        style="margin-left: 8px"
      >
        Добавить
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, markRaw } from 'vue'
import { ElMessageBox, ElMessage } from 'element-plus'
import { Edit, Delete, RemoveFilled } from '@element-plus/icons-vue'
import { dictionariesApi, type DictionaryItem, type DictionaryType } from '@/api/dictionaries'

const props = defineProps<{
  type: DictionaryType
  showLevel?: boolean
}>()

const emit = defineEmits<{
  (e: 'change'): void
}>()

const EditIcon = markRaw(Edit)
const DeleteIcon = markRaw(Delete)

const items = ref<DictionaryItem[]>([])
const loading = ref(false)
const saving = ref(false)
const adding = ref(false)

const editingId = ref<string | null>(null)
const editName = ref('')
const editLevel = ref<number | undefined>(undefined)

const newName = ref('')
const newLevel = ref<number | undefined>(undefined)

async function load() {
  loading.value = true
  try {
    items.value = await dictionariesApi.getAll(props.type, false)
  } finally {
    loading.value = false
  }
}

load()

function startEdit(row: DictionaryItem) {
  editingId.value = row.id
  editName.value = row.name
  editLevel.value = row.level ?? undefined
}

function cancelEdit() {
  editingId.value = null
}

async function saveEdit(row: DictionaryItem) {
  if (!editName.value.trim()) return
  saving.value = true
  try {
    const updated = await dictionariesApi.update(
      props.type,
      row.id,
      editName.value.trim(),
      props.showLevel ? editLevel.value : undefined,
    )
    const idx = items.value.findIndex((i) => i.id === row.id)
    if (idx !== -1) items.value[idx] = updated
    editingId.value = null
    emit('change')
  } finally {
    saving.value = false
  }
}

async function handleDeactivate(row: DictionaryItem) {
  await ElMessageBox.confirm(
    `Деактивировать "${row.name}"? Значение перестанет отображаться в фильтрах.`,
    'Деактивация',
    { confirmButtonText: 'Деактивировать', cancelButtonText: 'Отмена', type: 'warning' },
  )
  await dictionariesApi.deactivate(props.type, row.id)
  const idx = items.value.findIndex((i) => i.id === row.id)
  if (idx !== -1) items.value[idx] = { ...items.value[idx], is_active: false }
  ElMessage.success('Значение деактивировано')
  emit('change')
}

async function handleAdd() {
  if (!newName.value.trim()) return
  adding.value = true
  try {
    const created = await dictionariesApi.create(
      props.type,
      newName.value.trim(),
      props.showLevel ? newLevel.value : undefined,
    )
    items.value.push(created)
    newName.value = ''
    newLevel.value = undefined
    ElMessage.success('Значение добавлено')
    emit('change')
  } catch {
    // error already shown by axios interceptor
  } finally {
    adding.value = false
  }
}
</script>

<style scoped>
.dictionary-editor {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.add-row {
  display: flex;
  align-items: center;
  padding: 8px 0;
}

.text-inactive {
  color: #9ca3af;
}

.icon-inactive {
  margin-left: 4px;
  vertical-align: middle;
  color: #9ca3af;
}
</style>
