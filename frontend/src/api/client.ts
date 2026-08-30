import { getAccessToken } from '@/auth/session'

export interface Overview {
  filings: number
  verifications: number
  pendingReviews: number
  discrepancies: number
}

export interface VerificationSummary {
  runId: string
  filingId: string
  factName: string
  difference: number
  tolerance: number
  status: string
  citation: string
  reviewStatus: string
  createdAt: string
}

export interface VerificationInput {
  filingId: string
  factName: string
  actualValue: number
  expectedValue: number
  tolerance: number
  unit: string
  citation: string
}

export interface VerificationResponse {
  runId: string
  filingId: string
  factName: string
  difference: number
  tolerance: number
  status: string
  citation: string
}

export interface FilingSummary {
  documentVersionId: string
  filingId: string
  form: string
  format: string
  version: string
  createdAt: string
}

export interface PageResponse<T> {
  items: T[]
  page: number
  size: number
  total: number
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = getAccessToken()
  const headers = new Headers(init.headers)
  if (token) headers.set('Authorization', `Bearer ${token}`)
  if (init.body && !(init.body instanceof FormData)) headers.set('Content-Type', 'application/json')

  const response = await fetch(path, { ...init, headers })
  if (!response.ok) {
    const detail = await response.text()
    throw new Error(detail || `HTTP ${response.status}`)
  }
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

export const getOverview = () => request<Overview>('/api/overview')
export const listFilings = () => request<PageResponse<FilingSummary>>('/api/filings?page=0&size=50')
export const listVerifications = () => request<PageResponse<VerificationSummary>>('/api/verification-runs?page=0&size=50')
export const createVerification = (input: VerificationInput) => request<VerificationResponse>('/api/verification-runs', {
  method: 'POST',
  body: JSON.stringify(input),
})
export const getTimeline = (runId: string) => request<Array<{ eventType: string; detail: string; createdAt: string }>>(`/api/verification-runs/${encodeURIComponent(runId)}/timeline`)
export const reviewVerification = (runId: string, decision: string, comment: string) => request(`/api/verification-runs/${encodeURIComponent(runId)}/review-decisions`, {
  method: 'POST',
  body: JSON.stringify({ decision, comment }),
})

export async function uploadFiling(file: File, metadata: Record<string, string>) {
  const data = new FormData()
  data.append('file', file)
  Object.entries(metadata).forEach(([key, value]) => data.append(key, value))
  return request('/api/filings/upload', { method: 'POST', body: data })
}
