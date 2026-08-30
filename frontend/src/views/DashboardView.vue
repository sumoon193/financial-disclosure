<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { AlertCircle, CheckCircle2, FileText, SearchCheck } from 'lucide-vue-next'
import StatePanel from '@/components/StatePanel.vue'
import { getOverview, listVerifications, type Overview, type VerificationSummary } from '@/api/client'

const overview = ref<Overview | null>(null)
const runs = ref<VerificationSummary[]>([])
const loading = ref(true)
const failed = ref(false)

const metrics = computed(() => [
  { label: '申报文件', value: overview.value?.filings ?? 0, icon: FileText, test: 'metric-filings' },
  { label: '核验运行', value: overview.value?.verifications ?? 0, icon: SearchCheck },
  { label: '待复核', value: overview.value?.pendingReviews ?? 0, icon: AlertCircle, test: 'metric-pending' },
  { label: '差异项', value: overview.value?.discrepancies ?? 0, icon: CheckCircle2 },
])

async function load() {
  loading.value = true
  failed.value = false
  try {
    const [summary, verificationPage] = await Promise.all([getOverview(), listVerifications()])
    overview.value = summary
    runs.value = verificationPage.items
  } catch {
    failed.value = true
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="page-stack">
    <StatePanel v-if="failed" kind="error" title="无法连接核验服务" detail="请检查后端、身份服务和数据库状态。" @retry="load" />
    <template v-else>
      <section class="metrics-grid" aria-label="业务指标">
        <article v-for="metric in metrics" :key="metric.label" class="metric" :data-testid="metric.test">
          <component :is="metric.icon" :size="20" />
          <span>{{ metric.label }}</span>
          <strong>{{ loading ? '—' : metric.value }}</strong>
        </article>
      </section>

      <section class="work-section">
        <div class="section-heading">
          <div><p class="eyebrow">REVIEW QUEUE</p><h2>待处理核验</h2></div>
          <RouterLink class="text-link" to="/verifications">查看全部</RouterLink>
        </div>
        <div v-if="loading" class="loading-lines" aria-label="加载中"><i /><i /><i /></div>
        <StatePanel v-else-if="runs.length === 0" kind="empty" title="暂无核验记录" detail="导入或上传申报文件后，核验结果会出现在这里。" />
        <div v-else class="data-table-wrap">
          <table class="data-table">
            <thead><tr><th>事实项</th><th>状态</th><th>差异</th><th>引用</th><th>复核</th></tr></thead>
            <tbody>
              <tr v-for="run in runs.slice(0, 8)" :key="run.runId">
                <td><strong>{{ run.factName }}</strong><small>{{ run.filingId }}</small></td>
                <td><span class="status" :data-status="run.status">{{ run.status }}</span></td>
                <td>{{ run.difference }} / {{ run.tolerance }}</td>
                <td class="mono">{{ run.citation }}</td>
                <td><span class="status" :data-status="run.reviewStatus">{{ run.reviewStatus === 'pending' ? '待复核' : run.reviewStatus }}</span></td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </template>
  </div>
</template>
