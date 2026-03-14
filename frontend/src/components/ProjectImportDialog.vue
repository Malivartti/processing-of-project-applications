<template>
  <el-dialog
    :model-value="modelValue"
    title="Импорт проектов из Excel"
    width="620px"
    :close-on-click-modal="false"
    @update:model-value="$emit('update:modelValue', $event)"
    @closed="onClosed"
  >
    <!-- Step 1: File selection -->
    <template v-if="!preview">
      <el-upload
        ref="uploadRef"
        drag
        accept=".xlsx"
        :auto-upload="false"
        :limit="1"
        :on-change="onFileChange"
        :on-exceed="onExceed"
        :file-list="fileList"
      >
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">
          Перетащите .xlsx файл сюда или <em>нажмите для выбора</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            Только файлы .xlsx, максимум 50 МБ.
            <el-button link type="primary" @click.stop="downloadTemplate">
              Скачать шаблон
            </el-button>
          </div>
        </template>
      </el-upload>
    </template>

    <!-- Step 2: Preview -->
    <template v-else>
      <el-alert
        :title="`Готово к импорту: ${preview.valid_count} строк`"
        :type="preview.valid_count > 0 ? 'success' : 'warning'"
        :closable="false"
        show-icon
        style="margin-bottom: 12px"
      />

      <el-alert
        v-if="preview.duplicates.length > 0"
        :title="`Предупреждение: ${preview.duplicates.length} дубликатов по названию`"
        type="warning"
        :closable="false"
        show-icon
        style="margin-bottom: 12px"
      >
        <template #default>
          <div style="margin-top: 4px; font-size: 12px; color: #666">
            {{ preview.duplicates.slice(0, 5).join(', ') }}
            <span v-if="preview.duplicates.length > 5">...и ещё {{ preview.duplicates.length - 5 }}</span>
          </div>
        </template>
      </el-alert>

      <template v-if="preview.errors.length > 0">
        <div style="margin-bottom: 8px; font-weight: 500; color: #f56c6c">
          Ошибки ({{ preview.error_count }}):
        </div>
        <el-scrollbar max-height="200px">
          <el-table :data="preview.errors" size="small" border>
            <el-table-column prop="row" label="Строка" width="70" align="center" />
            <el-table-column prop="field" label="Поле" width="160" />
            <el-table-column prop="message" label="Сообщение" />
          </el-table>
        </el-scrollbar>
      </template>

      <el-button
        link
        type="primary"
        style="margin-top: 12px"
        @click="resetToFileSelect"
      >
        ← Выбрать другой файл
      </el-button>
    </template>

    <template #footer>
      <el-button @click="$emit('update:modelValue', false)">Отмена</el-button>

      <template v-if="!preview">
        <el-button
          type="primary"
          :loading="loading"
          :disabled="!selectedFile"
          @click="doPreview"
        >
          Проверить
        </el-button>
      </template>

      <template v-else>
        <el-button
          type="primary"
          :loading="loading"
          :disabled="preview.valid_count === 0"
          @click="doImport"
        >
          Импортировать {{ preview.valid_count }} проектов
        </el-button>
      </template>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import type { UploadFile, UploadInstance } from 'element-plus'
import { importApi, type ImportPreviewResponse } from '../api/import'

defineProps<{ modelValue: boolean }>()
const emit = defineEmits<{
  (e: 'update:modelValue', v: boolean): void
  (e: 'imported'): void
}>()

const uploadRef = ref<UploadInstance>()
const selectedFile = ref<File | null>(null)
const fileList = ref<UploadFile[]>([])
const preview = ref<ImportPreviewResponse | null>(null)
const loading = ref(false)

function onFileChange(file: UploadFile) {
  selectedFile.value = file.raw ?? null
}

function onExceed() {
  ElMessage.warning('Можно загрузить только один файл')
}

function downloadTemplate() {
  importApi.downloadTemplate()
}

async function doPreview() {
  if (!selectedFile.value) return
  loading.value = true
  try {
    preview.value = await importApi.preview(selectedFile.value)
  } catch {
    // axios interceptor handles toast
  } finally {
    loading.value = false
  }
}

async function doImport() {
  if (!selectedFile.value || !preview.value) return
  loading.value = true
  try {
    const result = await importApi.confirm(selectedFile.value)
    ElMessage.success(`Импортировано ${result.valid_count} проектов`)
    emit('update:modelValue', false)
    emit('imported')
  } catch {
    // axios interceptor handles toast
  } finally {
    loading.value = false
  }
}

function resetToFileSelect() {
  preview.value = null
  selectedFile.value = null
  fileList.value = []
  uploadRef.value?.clearFiles()
}

function onClosed() {
  resetToFileSelect()
}
</script>
