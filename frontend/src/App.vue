<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { Activity, FileSearch, Files, Gauge, LogOut, ShieldCheck } from 'lucide-vue-next'
import { isOidcConfigured, logout } from '@/auth/session'

const route = useRoute()
const links = [
  { to: '/', label: '审计总览', icon: Gauge },
  { to: '/filings', label: '申报文件', icon: Files },
  { to: '/verifications', label: '核验与复核', icon: FileSearch },
  { to: '/operations', label: '评测与设施', icon: Activity },
]
const title = computed(() => String(route.meta.title ?? 'Financial Disclosure'))
</script>

<template>
  <div class="app-shell">
    <aside class="side-nav">
      <div class="brand"><span class="brand-mark">FD</span><div><strong>Financial Disclosure</strong><small>财务披露核验平台</small></div></div>
      <nav aria-label="主导航"><RouterLink v-for="link in links" :key="link.to" :to="link.to"><component :is="link.icon" :size="18" />{{ link.label }}</RouterLink></nav>
      <div class="auth-state"><ShieldCheck :size="18" /><div><strong>{{ isOidcConfigured() ? 'OIDC 已配置' : 'OIDC 未配置' }}</strong><small>令牌仅保存在内存</small></div></div>
    </aside>
    <div class="workspace">
      <header class="topbar"><div><p class="eyebrow">FINANCIAL CONTROL ROOM</p><h1>{{ title }}</h1></div><button v-if="isOidcConfigured()" class="icon-button" title="退出登录" @click="logout"><LogOut :size="18" /></button></header>
      <main><RouterView /></main>
    </div>
  </div>
</template>
