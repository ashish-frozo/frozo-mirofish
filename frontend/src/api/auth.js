import service from './index'

export const signup = (data) => service.post('/api/auth/signup', data)
export const login = (data) => service.post('/api/auth/login', data)
export const refreshToken = (token) => service.post('/api/auth/refresh', { refresh_token: token })
export const logout = () => service.post('/api/auth/logout')
export const getMe = () => service.get('/api/auth/me')
export const updateMe = (data) => service.put('/api/auth/me', data)
