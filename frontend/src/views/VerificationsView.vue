<script setup lang="ts">
import { onMounted, ref } from 'vue'
import StatePanel from '@/components/StatePanel.vue'
import {
  createVerification,
  getTimeline,
  listVerifications,
  reviewVerification,
  type VerificationSummary,
} from '@/api/client'

const runs = ref<VerificationSummary[]>([])
const selected = ref<VerificationSummary | null>(null)
const timeline = ref<Array<{ eventType: string; detail: string; createdAt: string }>>([])
const failed = ref(false)
const creating = ref(false)
const createError = ref('')
const reviewComment = ref('')
const reviewError = ref('')
const draft = ref({
  filingId: '',
  factName: '',
  actualValue: '',
  expectedValue: '',
  tolerance: '0.01',
  unit: 'USD',
  citation: '',
})

async function load() { try { runs.value = (await listVerifications()).items } catch { failed.value = true } }
async function inspect(run: VerificationSummary) { selected.value = run; reviewComment.value = ''; reviewError.value = ''; timeline.value = await getTimeline(run.runId) }
async function createRun() {
  createError.value = ''
  const actualValue = Number(draft.value.actualValue)
  const expectedValue = Number(draft.value.expectedValue)
  const tolerance = Number(draft.value.tolerance)
  if (!Number.isFinite(actualValue) || !Number.isFinite(expectedValue) || !Number.isFinite(tolerance) || tolerance < 0) {
    createError.value = '请输入有效的实际值、期望值和非负容差。'
    return
  }
  creating.value = true
  try {
    await createVerification({
      filingId: draft.value.filingId.trim(),
      factName: draft.value.factName.trim(),
      actualValue,
      expectedValue,
      tolerance,
      unit: draft.value.unit.trim(),
      citation: draft.value.citation.trim(),
    })
    await load()
  } catch (error) {
    createError.value = error instanceof Error ? error.message : '创建核验失败。'
  } finally {
    creating.value = false
  }
}
async function decide(decision: 'approved' | 'rejected') {
  if (!selected.value) return
  reviewError.value = ''
  if (!reviewComment.value.trim()) { reviewError.value = '请填写复核意见'; return }
  try {
    await reviewVerification(selected.value.runId, decision, reviewComment.value.trim())
    selected.value = null
    await load()
  } catch (error) { reviewError.value = error instanceof Error ? error.message : '复核提交失败' }
}
onMounted(load)
</script>

<template>
  <div class="page-stack split-workspace">
    <section class="work-section">
      <div class="section-heading"><div><p class="eyebrow">DETERMINISTIC CHECKS</p><h2>核验运行</h2></div></div>
      <form class="verification-form" data-testid="create-verification" @submit.prevent="createRun">
        <label>申报 ID<input v-model="draft.filingId" name="filingId" required /></label>
        <label>事实名称<input v-model="draft.factName" name="factName" required /></label>
        <label>实际值<input v-model="draft.actualValue" name="actualValue" inputmode="decimal" required /></label>
        <label>期望值<input v-model="draft.expectedValue" name="expectedValue" inputmode="decimal" required /></label>
        <label>容差<input v-model="draft.tolerance" name="tolerance" inputmode="decimal" required /></label>
        <label>单位<input v-model="draft.unit" name="unit" required /></label>
        <label class="citation-field">引用<input v-model="draft.citation" name="citation" required /></label>
        <div class="verification-actions"><p v-if="createError" role="alert">{{ createError }}</p><button class="button" type="submit" :disabled="creating">{{ creating ? '创建中' : '创建核验' }}</button></div>
      </form>
      <StatePanel v-if="failed" kind="error" title="无法读取核验运行" detail="请检查 API 和数据库。" @retry="load" />
      <StatePanel v-else-if="runs.length === 0" kind="empty" title="暂无核验" detail="核验任务产生后会显示 Decimal 计算与引用。" />
      <button v-for="run in runs" v-else :key="run.runId" class="run-row" type="button" @click="inspect(run)">
        <span><strong>{{ run.factName }}</strong><small>{{ run.citation }}</small></span><span class="status" :data-status="run.reviewStatus">{{ run.reviewStatus }}</span>
      </button>
    </section>
    <aside class="evidence-pane">
      <template v-if="selected">
        <p class="eyebrow">AUDIT TIMELINE</p><h2>{{ selected.factName }}</h2>
        <dl class="fact-grid"><div><dt>差异</dt><dd>{{ selected.difference }}</dd></div><div><dt>容差</dt><dd>{{ selected.tolerance }}</dd></div><div><dt>状态</dt><dd>{{ selected.status }}</dd></div></dl>
        <ol class="timeline"><li v-for="event in timeline" :key="event.createdAt + event.eventType"><strong>{{ event.eventType }}</strong><p>{{ event.detail }}</p><time>{{ event.createdAt }}</time></li></ol>
        <label class="review-comment">复核意见<textarea v-model="reviewComment" name="reviewComment" rows="3" required /></label>
        <p v-if="reviewError" class="review-error" role="alert">{{ reviewError }}</p>
        <div class="button-row"><button class="button" @click="decide('approved')">通过复核</button><button class="button button--danger" @click="decide('rejected')">驳回</button></div>
      </template>
      <StatePanel v-else kind="empty" title="选择核验记录" detail="右侧将展示确定性计算、引用和完整事件时间线。" />
    </aside>
  </div>
</template>

<style scoped>
.verification-form { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:10px; padding:14px; margin:0 0 16px; background:#f7f9f9; border:1px solid #dce3e3; }
.verification-form label { display:grid; gap:5px; color:#516166; font-size:12px; font-weight:700; }
.verification-form input { width:100%; min-width:0; padding:8px 9px; border:1px solid #b8c5c7; border-radius:4px; background:#fff; color:#1d2c30; font:inherit; }
.verification-form input:focus { outline:2px solid #78aebe; outline-offset:1px; }
.citation-field { grid-column:span 2; }
.verification-actions { display:flex; align-items:end; justify-content:space-between; gap:8px; }
.verification-actions p { margin:0; color:#a2332d; font-size:12px; }
.review-comment { display:grid; gap:5px; margin:16px 0 8px; color:#516166; font-size:12px; font-weight:700; }
.review-comment textarea { width:100%; min-height:72px; resize:vertical; padding:8px 9px; border:1px solid #b8c5c7; border-radius:4px; font:inherit; }
.review-error { margin:0 0 8px; color:#a2332d; font-size:12px; }
@media (max-width:900px) { .verification-form { grid-template-columns:repeat(2,minmax(0,1fr)); }.citation-field { grid-column:span 1; } }
@media (max-width:540px) { .verification-form { grid-template-columns:1fr; }.verification-actions { align-items:stretch; flex-direction:column; }.verification-actions .button { width:100%; } }
</style>
