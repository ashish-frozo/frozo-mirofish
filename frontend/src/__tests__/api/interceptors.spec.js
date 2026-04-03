import { describe, it, expect, vi, beforeEach } from 'vitest'
import { requestWithRetry } from '../../api/index'

describe('requestWithRetry', () => {
  beforeEach(() => {
    vi.useRealTimers()
  })

  it('succeeds on first try', async () => {
    const fn = vi.fn().mockResolvedValue({ data: 'ok' })

    const result = await requestWithRetry(fn, 3, 1000)

    expect(result).toEqual({ data: 'ok' })
    expect(fn).toHaveBeenCalledTimes(1)
  })

  it('retries on failure and eventually succeeds', async () => {
    const fn = vi.fn()
      .mockRejectedValueOnce(new Error('fail 1'))
      .mockResolvedValue({ data: 'recovered' })

    // Use minimal delay so real timers resolve quickly
    const result = await requestWithRetry(fn, 3, 1)

    expect(result).toEqual({ data: 'recovered' })
    expect(fn).toHaveBeenCalledTimes(2)
  })

  it('throws after max retries exhausted', async () => {
    const fn = vi.fn().mockRejectedValue(new Error('persistent failure'))

    await expect(requestWithRetry(fn, 3, 1)).rejects.toThrow('persistent failure')
    expect(fn).toHaveBeenCalledTimes(3)
  })
})
