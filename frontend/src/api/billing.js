import service from './index'

export const createCheckout = (plan) => service.post('/api/billing/checkout', { plan })
export const createPortal = () => service.post('/api/billing/portal')
export const getBillingStatus = () => service.get('/api/billing/status')
