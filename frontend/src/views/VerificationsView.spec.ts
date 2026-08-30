import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'

import VerificationsView from './VerificationsView.vue'
import * as api from '@/api/client'

describe('VerificationsView', () => {
  afterEach(() => vi.restoreAllMocks())

  it('submits deterministic verification input and refreshes the tenant run list', async () => {
    vi.spyOn(api, 'listVerifications').mockResolvedValue({
      items: [], page: 0, size: 50, total: 0,
    })
    const createVerification = vi.spyOn(api, 'createVerification').mockResolvedValue({
      runId: 'run-1', filingId: 'filing-1', factName: 'Revenue',
      difference: 0, tolerance: 0.01, status: 'passed', citation: 'filing-1#revenue',
    })

    const wrapper = mount(VerificationsView)
    await flushPromises()

    await wrapper.get('[name="filingId"]').setValue('filing-1')
    await wrapper.get('[name="factName"]').setValue('Revenue')
    await wrapper.get('[name="actualValue"]').setValue('100.00')
    await wrapper.get('[name="expectedValue"]').setValue('100.00')
    await wrapper.get('[name="tolerance"]').setValue('0.01')
    await wrapper.get('[name="unit"]').setValue('USD')
    await wrapper.get('[name="citation"]').setValue('filing-1#revenue')
    await wrapper.get('[data-testid="create-verification"]').trigger('submit')
    await flushPromises()

    expect(createVerification).toHaveBeenCalledWith({
      filingId: 'filing-1',
      factName: 'Revenue',
      actualValue: 100,
      expectedValue: 100,
      tolerance: 0.01,
      unit: 'USD',
      citation: 'filing-1#revenue',
    })
    expect(api.listVerifications).toHaveBeenCalledTimes(2)
  })
})
