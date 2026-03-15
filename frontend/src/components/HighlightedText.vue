<template>
  <span v-if="!text" class="text-empty">—</span>
  <span v-else>
    <template v-for="(part, i) in parts" :key="i">
      <mark v-if="part.highlight" class="keyword-highlight">{{ part.text }}</mark>
      <span v-else>{{ part.text }}</span>
    </template>
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  text: string | null | undefined
  keywords: string[]
}>()

interface TextPart {
  text: string
  highlight: boolean
}

const parts = computed((): TextPart[] => {
  if (!props.text || !props.keywords.length) {
    return [{ text: props.text ?? '', highlight: false }]
  }

  // Build a regex that matches any keyword (word boundary, case-insensitive)
  const escaped = props.keywords.map((k) => k.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'))
  const pattern = new RegExp(`(${escaped.join('|')})`, 'gi')

  const result: TextPart[] = []
  let last = 0
  let match: RegExpExecArray | null

  while ((match = pattern.exec(props.text)) !== null) {
    if (match.index > last) {
      result.push({ text: props.text.slice(last, match.index), highlight: false })
    }
    result.push({ text: match[0], highlight: true })
    last = match.index + match[0].length
  }

  if (last < props.text.length) {
    result.push({ text: props.text.slice(last), highlight: false })
  }

  return result
})
</script>

<style scoped>
.keyword-highlight {
  background-color: #fef08a;
  color: inherit;
  padding: 0 1px;
  border-radius: 2px;
}

.text-empty {
  color: #909399;
}
</style>
