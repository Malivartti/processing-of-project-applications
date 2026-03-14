<template>
  <div class="project-filters">
    <el-row :gutter="12" align="middle">
      <el-col :span="6">
        <el-input
          v-model="searchInput"
          placeholder="Поиск по названию..."
          clearable
          prefix-icon="Search"
          @input="onSearchInput"
          @clear="onSearchClear"
        />
      </el-col>

      <el-col :span="4">
        <el-select
          v-model="localFilters.direction_id"
          placeholder="Направление"
          clearable
          @change="onFilterChange"
        >
          <el-option
            v-for="item in directions"
            :key="item.id"
            :label="item.name"
            :value="item.id"
          />
        </el-select>
      </el-col>

      <el-col :span="4">
        <el-select
          v-model="localFilters.priority_direction_id"
          placeholder="Приоритетное направление"
          clearable
          @change="onFilterChange"
        >
          <el-option
            v-for="item in priorityDirections"
            :key="item.id"
            :label="item.name"
            :value="item.id"
          />
        </el-select>
      </el-col>

      <el-col :span="3">
        <el-select
          v-model="localFilters.trl_id"
          placeholder="УГТ"
          clearable
          @change="onFilterChange"
        >
          <el-option
            v-for="item in trlLevels"
            :key="item.id"
            :label="item.name"
            :value="item.id"
          />
        </el-select>
      </el-col>

      <el-col :span="3">
        <el-select
          v-model="isOngoingValue"
          placeholder="Срок"
          clearable
          @change="onIsOngoingChange"
        >
          <el-option label="Бессрочный" value="true" />
          <el-option label="Срочный" value="false" />
        </el-select>
      </el-col>

      <el-col :span="3">
        <el-select
          v-model="hasGroupValue"
          placeholder="Группа"
          clearable
          @change="onHasGroupChange"
        >
          <el-option label="В группе" value="true" />
          <el-option label="Без группы" value="false" />
        </el-select>
      </el-col>

      <el-col :span="3">
        <el-select
          v-model="localFilters.group_source"
          placeholder="Тип группы"
          clearable
          @change="onFilterChange"
        >
          <el-option label="Авто" value="auto" />
          <el-option label="Ручная" value="manual" />
        </el-select>
      </el-col>
    </el-row>

    <el-row v-if="hasActiveFilters" :gutter="12" style="margin-top: 8px">
      <el-col :span="24">
        <el-button size="small" type="info" plain @click="onReset">
          Сбросить фильтры
        </el-button>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { dictionariesApi, type DictionaryItem } from '../api/dictionaries'
import type { ProjectsFilters } from '../stores/projects'

const emit = defineEmits<{
  change: [filters: Partial<ProjectsFilters>]
  reset: []
}>()

const props = defineProps<{
  initialFilters: ProjectsFilters
}>()

const directions = ref<DictionaryItem[]>([])
const priorityDirections = ref<DictionaryItem[]>([])
const trlLevels = ref<DictionaryItem[]>([])

const localFilters = reactive({
  direction_id: props.initialFilters.direction_id,
  priority_direction_id: props.initialFilters.priority_direction_id,
  trl_id: props.initialFilters.trl_id,
  group_source: props.initialFilters.group_source,
})

const searchInput = ref(props.initialFilters.search)
const isOngoingValue = ref<string | null>(
  props.initialFilters.is_ongoing === null ? null : String(props.initialFilters.is_ongoing),
)
const hasGroupValue = ref<string | null>(
  props.initialFilters.has_group === null ? null : String(props.initialFilters.has_group),
)

const hasActiveFilters = computed(
  () =>
    searchInput.value ||
    localFilters.direction_id ||
    localFilters.priority_direction_id ||
    localFilters.trl_id ||
    isOngoingValue.value !== null ||
    hasGroupValue.value !== null ||
    localFilters.group_source,
)

let searchTimeout: ReturnType<typeof setTimeout> | null = null

function onSearchInput() {
  if (searchTimeout) clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    emit('change', { search: searchInput.value })
  }, 300)
}

function onSearchClear() {
  if (searchTimeout) clearTimeout(searchTimeout)
  emit('change', { search: '' })
}

function onFilterChange() {
  emit('change', {
    direction_id: localFilters.direction_id,
    priority_direction_id: localFilters.priority_direction_id,
    trl_id: localFilters.trl_id,
    group_source: localFilters.group_source,
  })
}

function onIsOngoingChange(val: string | null) {
  emit('change', { is_ongoing: val === null ? null : val === 'true' })
}

function onHasGroupChange(val: string | null) {
  emit('change', { has_group: val === null ? null : val === 'true' })
}

function onReset() {
  searchInput.value = ''
  isOngoingValue.value = null
  hasGroupValue.value = null
  Object.assign(localFilters, {
    direction_id: null,
    priority_direction_id: null,
    trl_id: null,
    group_source: null,
  })
  emit('reset')
}

onMounted(async () => {
  const [d, pd, trl] = await Promise.all([
    dictionariesApi.getAll('directions'),
    dictionariesApi.getAll('priority_directions'),
    dictionariesApi.getAll('trl_levels'),
  ])
  directions.value = d
  priorityDirections.value = pd
  trlLevels.value = trl
})
</script>

<style scoped>
.project-filters {
  padding: 12px 0;
}

.el-select {
  width: 100%;
}
</style>
