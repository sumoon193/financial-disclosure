<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { Upload } from 'lucide-vue-next'
import StatePanel from '@/components/StatePanel.vue'
import { listFilings, uploadFiling, type FilingSummary } from '@/api/client'

const filings = ref<FilingSummary[]>([])
const failed = ref(false)
const busy = ref(false)
const fileInput = ref<HTMLInputElement>()

async function load() {
  failed.value = false
  try { filings.value = (await listFilings()).items } catch { failed.value = true }
}

async function chooseFile(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (!file) return
  busy.value = true
  try {
    const extension = file.name.split('.').pop()?.toLowerCase() ?? 'pdf'
    const format = ['xbrl', 'html', 'pdf'].includes(extension) ? extension : 'image'
    await uploadFiling(file, {
      filingId: file.name.replace(/\.[^.]+$/, ''),
      form: '10-K',
      format,
      version: new Date().toISOString().slice(0, 10),
    })
    await load()
  } finally { busy.value = false; if (fileInput.value) fileInput.value.value = '' }
}

onMounted(load)
</script>

<template>
  <div class="page-stack">
    <section class="action-bar">
      <div><p class="eyebrow">SOURCE REGISTRY</p><h2>申报文件</h2><p>统一查看文件来源、处理状态和入库时间。</p></div>
      <label class="button"><Upload :size="17" />{{ busy ? '上传中' : '上传文件' }}<input ref="fileInput" type="file" hidden :disabled="busy" @change="chooseFile" /></label>
    </section>
    <StatePanel v-if="failed" kind="error" title="无法读取申报文件" detail="服务恢复后可重新加载。" @retry="load" />
    <StatePanel v-else-if="filings.length === 0" kind="empty" title="还没有申报文件" detail="上传本地文件，或通过 SEC 导入接口创建第一条记录。" />
    <div v-else class="data-table-wrap">
      <table class="data-table"><thead><tr><th>申报标识</th><th>表单</th><th>格式</th><th>版本</th><th>入库时间</th></tr></thead>
        <tbody><tr v-for="filing in filings" :key="filing.documentVersionId"><td><strong>{{ filing.filingId }}</strong><small>{{ filing.documentVersionId }}</small></td><td>{{ filing.form }}</td><td>{{ filing.format }}</td><td>{{ filing.version }}</td><td>{{ filing.createdAt }}</td></tr></tbody>
      </table>
    </div>
  </div>
</template>
