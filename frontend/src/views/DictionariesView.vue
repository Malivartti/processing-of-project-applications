<template>
  <div class="dictionaries-view">
    <h2>Справочники</h2>
    <p class="subtitle">Управление значениями направлений, приоритетных направлений и уровней готовности технологий</p>

    <el-tabs>
      <el-tab-pane label="Направления" name="directions">
        <DictionaryEditor type="directions" @change="onDirectionsChange" />
      </el-tab-pane>

      <el-tab-pane label="Приоритетные направления" name="priority_directions">
        <DictionaryEditor type="priority_directions" @change="onDirectionsChange" />
      </el-tab-pane>

      <el-tab-pane label="УГТ (уровни готовности)" name="trl_levels">
        <DictionaryEditor type="trl_levels" :show-level="true" @change="onDirectionsChange" />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import DictionaryEditor from '@/components/DictionaryEditor.vue'

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
</style>
