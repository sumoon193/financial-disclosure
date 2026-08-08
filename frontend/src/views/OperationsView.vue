<script setup lang="ts">
const services = [
  ['PostgreSQL', '事实、核验与审计持久化'], ['Redis', '查询缓存与租约'], ['MinIO', '申报原文对象存储'],
  ['Tesseract', '本地 OCR'], ['SEC EDGAR', '外部申报来源'], ['Qwen', '确定性事实解释'], ['OpenTelemetry', '链路与指标'],
]
</script>
<template><div class="page-stack"><section class="work-section"><div class="section-heading"><div><p class="eyebrow">DEPENDENCIES</p><h2>基础设施边界</h2><p>此页面不伪造健康状态。具体可用性以独立 live smoke 和后端探针为准。</p></div></div><div class="service-list"><article v-for="service in services" :key="service[0]"><span class="status" data-status="blocked">待探测</span><div><strong>{{ service[0] }}</strong><p>{{ service[1] }}</p></div></article></div></section></div></template>
