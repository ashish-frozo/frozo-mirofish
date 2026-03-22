import service from './index'

export const startPrediction = (formData) => service.post('/api/predict', formData, {
  headers: { 'Content-Type': 'multipart/form-data' }
})

export const getPredictionStatus = (taskId) => service.get(`/api/predict/${taskId}/status`)

export const cancelPrediction = (taskId) => service.post(`/api/predict/${taskId}/cancel`)

export const getAccuracy = () => service.get('/api/predict/accuracy')
