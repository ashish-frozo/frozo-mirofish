import service from './index'

export const listProjects = (limit) =>
  service.get('/api/graph/project/list', { params: limit ? { limit } : {} })

export const getProject = (projectId) =>
  service.get(`/api/graph/project/${projectId}`)

export const deleteProject = (projectId) =>
  service.delete(`/api/graph/project/${projectId}`)
