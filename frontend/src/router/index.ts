import { createRouter, createWebHistory } from 'vue-router'

export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: () => import('@/views/DashboardView.vue'), meta: { title: '审计总览' } },
    { path: '/filings', component: () => import('@/views/FilingsView.vue'), meta: { title: '申报文件' } },
    { path: '/verifications', component: () => import('@/views/VerificationsView.vue'), meta: { title: '核验与复核' } },
    { path: '/operations', component: () => import('@/views/OperationsView.vue'), meta: { title: '评测与基础设施' } },
  ],
})
