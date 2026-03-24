<template>
  <div class="dictionaries-view">
    <h2>Справочники</h2>
    <p class="subtitle">
      Управление значениями направлений, приоритетных направлений, уровней
      готовности технологий и стоп-слов для генерации названий групп
    </p>

    <el-tabs>
      <el-tab-pane label="Направления" name="directions">
        <DictionaryEditor type="directions" @change="onDirectionsChange" />
      </el-tab-pane>

      <el-tab-pane label="Приоритетные направления" name="priority_directions">
        <DictionaryEditor
          type="priority_directions"
          @change="onDirectionsChange"
        />
      </el-tab-pane>

      <el-tab-pane label="УГТ (уровни готовности)" name="trl_levels">
        <DictionaryEditor
          type="trl_levels"
          :show-level="true"
          @change="onDirectionsChange"
        />
      </el-tab-pane>

      <el-tab-pane label="Стоп-слова" name="stopwords">
        <p class="tab-hint">
          Слова, которые исключаются при автоматической генерации названий групп.
          Базовый список (~175 слов) добавляется автоматически — здесь только доменные дополнения.
        </p>
        <DictionaryEditor type="stopwords" :tags-mode="true" @change="onDirectionsChange" />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import DictionaryEditor from "@/components/DictionaryEditor.vue";

function onDirectionsChange() {
  // filters in ProjectsView will reload dictionaries on next open
}
</script>

<style scoped>
.dictionaries-view {
  padding: 16px;
}

.subtitle {
  color: #6b7280;
  margin-bottom: 24px;
}

.tab-hint {
  color: #6b7280;
  font-size: 13px;
  margin-bottom: 12px;
}
</style>
