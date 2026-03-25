<template>
  <div class="project-filters">
    <div class="filters-search-row">
      <span class="filter-label">Поиск</span>
      <el-input
        v-model="searchInput"
        placeholder="Введите название, описание или ключевые слова..."
        clearable
        prefix-icon="Search"
        @input="onSearchInput"
        @clear="onSearchClear"
      />
    </div>

    <div class="filters-grid-row">
      <div class="filter-cell">
        <span class="filter-label">Направление</span>
        <el-select
          v-model="localFilters.direction_id"
          placeholder="Все"
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
      </div>

      <div class="filter-cell">
        <span class="filter-label">УГТ</span>
        <el-select
          v-model="localFilters.trl_id"
          placeholder="Все"
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
      </div>

      <div class="filter-cell">
        <span class="filter-label">Наличие группы</span>
        <el-select
          v-model="hasGroupValue"
          placeholder="Все"
          clearable
          @change="onHasGroupChange"
        >
          <el-option label="В группе" value="true" />
          <el-option label="Без группы" value="false" />
        </el-select>
      </div>

      <div class="filter-cell">
        <span class="filter-label">Тип группы</span>
        <el-select
          v-model="localFilters.group_source"
          placeholder="Все"
          clearable
          @change="onFilterChange"
        >
          <el-option label="Авто" value="auto" />
          <el-option label="Ручная" value="manual" />
        </el-select>
      </div>

      <div class="filter-cell filter-cell--reset">
        <el-button
          v-if="hasActiveFilters"
          size="small"
          type="info"
          plain
          @click="onReset"
        >
          Сбросить фильтры
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from "vue";
import { dictionariesApi, type DictionaryItem } from "../api/dictionaries";
import type { ProjectsFilters } from "../stores/projects";

const emit = defineEmits<{
  change: [filters: Partial<ProjectsFilters>];
  reset: [];
}>();

const props = defineProps<{
  initialFilters: ProjectsFilters;
}>();

const directions = ref<DictionaryItem[]>([]);
const trlLevels = ref<DictionaryItem[]>([]);

const localFilters = reactive({
  direction_id: props.initialFilters.direction_id,
  trl_id: props.initialFilters.trl_id,
  group_source: props.initialFilters.group_source,
});

const searchInput = ref(props.initialFilters.search);
const hasGroupValue = ref<string | null>(
  props.initialFilters.has_group === null
    ? null
    : String(props.initialFilters.has_group),
);

const hasActiveFilters = computed(
  () =>
    searchInput.value ||
    localFilters.direction_id ||
    localFilters.trl_id ||
    hasGroupValue.value !== null ||
    localFilters.group_source,
);

let searchTimeout: ReturnType<typeof setTimeout> | null = null;

function onSearchInput() {
  if (searchTimeout) clearTimeout(searchTimeout);
  searchTimeout = setTimeout(() => {
    emit("change", { search: searchInput.value });
  }, 300);
}

function onSearchClear() {
  if (searchTimeout) clearTimeout(searchTimeout);
  emit("change", { search: "" });
}

function onFilterChange() {
  emit("change", {
    direction_id: localFilters.direction_id,
    trl_id: localFilters.trl_id,
    group_source: localFilters.group_source,
  });
}

function onHasGroupChange(val: string | null) {
  emit("change", { has_group: val === null ? null : val === "true" });
}

function onReset() {
  searchInput.value = "";
  hasGroupValue.value = null;
  Object.assign(localFilters, {
    direction_id: null,
    trl_id: null,
    group_source: null,
  });
  emit("reset");
}

onMounted(async () => {
  const [d, trl] = await Promise.all([
    dictionariesApi.getAll("directions"),
    dictionariesApi.getAll("trl_levels"),
  ]);
  directions.value = d;
  trlLevels.value = trl;
});
</script>

<style scoped>
.project-filters {
  padding: 10px 0 4px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.filters-search-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
  width: 100%;
}

.filters-grid-row {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1fr auto;
  gap: 8px;
  align-items: end;
}

.filter-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.filter-cell .el-select {
  width: 100%;
}

.filter-label {
  font-size: 12px;
  color: #909399;
  line-height: 1;
}

.filter-cell--reset {
  justify-content: flex-end;
  padding-bottom: 1px;
}

@media (max-width: 900px) {
  .filters-grid-row {
    grid-template-columns: 1fr 1fr;
  }

  .filter-cell--reset {
    grid-column: 1 / -1;
    align-items: flex-start;
  }
}
</style>
