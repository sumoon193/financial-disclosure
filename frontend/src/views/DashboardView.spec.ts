import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'

import DashboardView from './DashboardView.vue'
import * as api from '@/api/client'

describe('Financial dashboard', () => {
  afterEach(() => vi.restoreAllMocks())

  it('renders persisted overview metrics and pending verification work', async () => {
    vi.spyOn(api, 'getOverview').mockResolvedValue({
      filings: 12,
      verifications: 31,
      pendingReviews: 4,
      discrepancies: 2,
    })
    vi.spyOn(api, 'listVerifications').mockResolvedValue({
      items: [
        {
          runId: 'run-1', filingId: 'filing-1', factName: 'Revenue',
          difference: 0.01, tolerance: 0.01, status: 'passed',
          citation: 'sec://filing-1', reviewStatus: 'pending',
          createdAt: '2026-08-07T00:00:00Z',
        },
      ],
      page: 0, size: 20, total: 1,
    })

    const wrapper = mount(DashboardView)
    await flushPromises()

    expect(wrapper.get('[data-testid="metric-filings"]').text()).toContain('12')
    expect(wrapper.get('[data-testid="metric-pending"]').text()).toContain('4')
    expect(wrapper.text()).toContain('Revenue')
    expect(wrapper.text()).toContain('待复核')
  })

  it('shows a retryable degraded state when the API is unavailable', async () => {
    vi.spyOn(api, 'getOverview').mockRejectedValue(new Error('unavailable'))
    vi.spyOn(api, 'listVerifications').mockRejectedValue(new Error('unavailable'))

    const wrapper = mount(DashboardView)
    await flushPromises()

    expect(wrapper.get('[role="alert"]').text()).toContain('无法连接核验服务')
    expect(wrapper.get('button').text()).toContain('重试')
  })
})
