import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAuthStore } from '../../store/auth'

// Mock the auth API module so the store can import it without side-effects
vi.mock('../../api/auth', () => ({
  signup: vi.fn(),
  login: vi.fn(),
  logout: vi.fn(),
  getMe: vi.fn(),
  refreshToken: vi.fn(),
}))

describe('Auth Store', () => {
  let store

  beforeEach(() => {
    // Clear localStorage and create a fresh Pinia instance for each test
    localStorage.clear()
    setActivePinia(createPinia())
    store = useAuthStore()
  })

  it('initial state is unauthenticated', () => {
    expect(store.isAuthenticated).toBe(false)
    expect(store.accessToken).toBeNull()
    expect(store.refreshTokenValue).toBeNull()
    expect(store.user).toBeNull()
  })

  it('setTokens stores tokens in reactive state and localStorage', () => {
    store.setTokens('access-abc', 'refresh-xyz')

    expect(store.accessToken).toBe('access-abc')
    expect(store.refreshTokenValue).toBe('refresh-xyz')
    expect(localStorage.getItem('access_token')).toBe('access-abc')
    expect(localStorage.getItem('refresh_token')).toBe('refresh-xyz')
  })

  it('isAuthenticated reflects token state', () => {
    expect(store.isAuthenticated).toBe(false)

    store.setTokens('tok', 'ref')
    expect(store.isAuthenticated).toBe(true)
  })

  it('clearTokens removes tokens from state and localStorage', () => {
    store.setTokens('tok', 'ref')
    store.clearTokens()

    expect(store.accessToken).toBeNull()
    expect(store.refreshTokenValue).toBeNull()
    expect(store.user).toBeNull()
    expect(localStorage.getItem('access_token')).toBeNull()
    expect(localStorage.getItem('refresh_token')).toBeNull()
  })

  it('isAuthenticated becomes false after clearTokens', () => {
    store.setTokens('tok', 'ref')
    expect(store.isAuthenticated).toBe(true)

    store.clearTokens()
    expect(store.isAuthenticated).toBe(false)
  })

  it('initializes accessToken from localStorage if present', () => {
    localStorage.setItem('access_token', 'persisted-token')
    localStorage.setItem('refresh_token', 'persisted-refresh')

    // Create a new store instance that reads from localStorage on init
    setActivePinia(createPinia())
    const freshStore = useAuthStore()

    expect(freshStore.accessToken).toBe('persisted-token')
    expect(freshStore.refreshTokenValue).toBe('persisted-refresh')
    expect(freshStore.isAuthenticated).toBe(true)
  })
})
