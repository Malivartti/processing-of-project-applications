<template>
  <div class="project-filters">
    <div class="filters-row">
      <el-input
        v-model="searchInput"
        class="filter-search"
        placeholder="Поиск по названию..."
        clearable
        prefix-icon="Search"
        @input="onSearchInput"
        @clear="onSearchClear"
      />

      <el-select
        v-model="localFilters.direction_id"
        class="filter-item"
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

      <el-select
        v-model="localFilters.trl_id"
        class="filter-item filter-item--narrow"
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

      <el-select
        v-model="hasGroupValue"
        class="filter-item filter-item--narrow"
        placeholder="Группа"
        clearable
        @change="onHasGroupChange"
      >
        <el-option label="В группе" value="true" />
        <el-option label="Без группы" value="false" />
      </el-select>

      <el-select
        v-model="localFilters.group_source"
        class="filter-item filter-item--narrow"
        placeholder="Тип группы"
        clearable
        @change="onFilterChange"
      >
        <el-option label="Авто" value="auto" />
        <el-option label="Ручная" value="manual" />
      </el-select>

      <el-button v-if="hasActiveFilters" size="small" type="info" plain @click="onReset">
        Сбросить
      </el-button>
    </div>
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
const trlLevels = ref<DictionaryItem[]>([])

const localFilters = reactive({
  direction_id: props.initialFilters.direction_id,
  trl_id: props.initialFilters.trl_id,
  group_source: props.initialFilters.group_source,
})

const searchInput = ref(props.initialFilters.search)
const hasGroupValue = ref<string | null>(
  props.initialFilters.has_group === null ? null : String(props.initialFilters.has_group),
)

const hasActiveFilters = computed(
  () =>
    searchInput.value ||
    localFilters.direction_id ||
    localFilters.trl_id ||
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
    trl_id: localFilters.trl_id,
    group_source: localFilters.group_source,
  })
}

function onHasGroupChange(val: string | null) {
  emit('change', { has_group: val === null ? null : val === 'true' })
}

function onReset() {
  searchInput.value = ''
  hasGroupValue.value = null
  Object.assign(localFilters, {
    direction_id: null,
    trl_id: null,
    group_source: null,
  })
  emit('reset')
}

onMounted(async () => {
  const [d, trl] = await Promise.all([
    dictionariesApi.getAll('directions'),
    dictionariesApi.getAll('trl_levels'),
  ])
  directions.value = d
  trlLevels.value = trl
})
</script>

<style scoped>
.project-filters {
  padding: 12px 0;
}

.filters-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.filter-search {
  flex: 2 1 200px;
  min-width: 180px;
}

.filter-item {
  flex: 1 1 150px;
  min-width: 140px;
}

.filter-item--wide {
  flex: 1.5 1 180px;
  min-width: 160px;
}

.filter-item--narrow {
  flex: 1 1 120px;
  min-width: 110px;
}
</style>
