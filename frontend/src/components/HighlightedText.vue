<template>
  <span v-if="!text" class="text-empty">—</span>
  <span v-else>
    <template v-for="(part, i) in parts" :key="i">
      <mark v-if="part.highlight === 'keyword'" class="keyword-highlight">{{ part.text }}</mark>
      <mark v-else-if="part.highlight === 'substring'" class="substring-highlight">{{ part.text }}</mark>
      <span v-else>{{ part.text }}</span>
    </template>
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  text: string | null | undefined
  keywords?: string[]
  substrings?: string[]
}>()

interface TextPart {
  text: string
  highlight: 'keyword' | 'substring' | null
}

const parts = computed((): TextPart[] => {
  if (!props.text) return [{ text: props.text ?? '', highlight: null }]

  const len = props.text.length
  const marks = new Array<'keyword' | 'substring' | null>(len).fill(null)

  // Mark keywords (yellow)
  const keywords = props.keywords ?? []
  if (keywords.length) {
    const escaped = keywords.map((k) => k.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'))
    const pattern = new RegExp(`(${escaped.join('|')})`, 'gi')
    let match: RegExpExecArray | null
    while ((match = pattern.exec(props.text)) !== null) {
      for (let i = match.index; i < match.index + match[0].length; i++) {
        marks[i] = 'keyword'
      }
    }
  }

  // Mark substrings (red) — overrides keywords
  const substrings = props.substrings ?? []
  if (substrings.length) {
    const escaped = substrings.map((s) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'))
    const pattern = new RegExp(`(${escaped.join('|')})`, 'gi')
    let match: RegExpExecArray | null
    while ((match = pattern.exec(props.text)) !== null) {
      for (let i = match.index; i < match.index + match[0].length; i++) {
        marks[i] = 'substring'
      }
    }
  }

  // Build parts from marks
  const result: TextPart[] = []
  let i = 0
  while (i < len) {
    const type = marks[i]
    let j = i + 1
    while (j < len && marks[j] === type) j++
    result.push({ text: props.text.slice(i, j), highlight: type })
    i = j
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

.substring-highlight {
  background-color: #fca5a5;
  color: inherit;
  padding: 0 1px;
  border-radius: 2px;
}

.text-empty {
  color: #909399;
}
</style>
