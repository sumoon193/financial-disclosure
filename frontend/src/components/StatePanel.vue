<script setup lang="ts">
import { AlertTriangle, Database, RefreshCw } from 'lucide-vue-next'

defineProps<{ kind: 'empty' | 'error' | 'blocked'; title: string; detail: string }>()
defineEmits<{ retry: [] }>()
</script>

<template>
  <section class="state-panel" :class="`state-panel--${kind}`" role="alert">
    <component :is="kind === 'empty' ? Database : AlertTriangle" :size="22" />
    <div>
      <strong>{{ title }}</strong>
      <p>{{ detail }}</p>
    </div>
    <button v-if="kind === 'error'" class="button button--quiet" type="button" @click="$emit('retry')">
      <RefreshCw :size="16" />重试
    </button>
  </section>
</template>
