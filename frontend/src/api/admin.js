import service from './index'

export const listPredictionCosts = (params = {}) =>
  service.get('/api/admin/predictions/costs', { params })

export const getPredictionCost = (taskId) =>
  service.get(`/api/admin/predictions/${taskId}/cost`)
