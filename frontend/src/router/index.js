import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Process from '../views/MainView.vue'
import SimulationView from '../views/SimulationView.vue'
import SimulationRunView from '../views/SimulationRunView.vue'
import ReportView from '../views/ReportView.vue'
import InteractionView from '../views/InteractionView.vue'
import { useAuthStore } from '../store/auth'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home,
    meta: { public: true }
  },
  {
    path: '/new',
    name: 'NewProject',
    component: Home
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { public: true }
  },
  {
    path: '/signup',
    name: 'Signup',
    component: () => import('../views/Signup.vue'),
    meta: { public: true }
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('../views/Dashboard.vue')
  },
  {
    path: '/process/:projectId',
    name: 'Process',
    component: Process,
    props: true
  },
  {
    path: '/simulation/:simulationId',
    name: 'Simulation',
    component: SimulationView,
    props: true
  },
  {
    path: '/simulation/:simulationId/start',
    name: 'SimulationRun',
    component: SimulationRunView,
    props: true
  },
  {
    path: '/report/:reportId',
    name: 'Report',
    component: ReportView,
    props: true
  },
  {
    path: '/interaction/:reportId',
    name: 'Interaction',
    component: InteractionView,
    props: true
  },
  {
    path: '/workspace/:projectId',
    name: 'Workspace',
    component: () => import('../views/WorkspaceView.vue'),
    props: true
  },
  {
    path: '/predict/:taskId',
    name: 'PredictionProgress',
    component: () => import('../views/PredictionProgress.vue'),
    props: true
  },
  {
    path: '/pricing',
    name: 'Pricing',
    component: () => import('../views/Pricing.vue'),
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach(async (to, from, next) => {
  const auth = useAuthStore()

  // Public routes don't need auth
  if (to.meta.public) {
    // If authenticated and going to login/signup, redirect to dashboard
    if (auth.isAuthenticated && (to.name === 'Login' || to.name === 'Signup')) {
      return next('/dashboard')
    }
    return next()
  }

  // Protected routes need auth
  if (!auth.isAuthenticated) {
    return next('/login')
  }

  // If we have a token but no user data, fetch it
  if (!auth.user) {
    await auth.fetchUser()
    if (!auth.isAuthenticated) {
      return next('/login')
    }
  }

  // Routes that require an active plan (creating new predictions)
  const planRequired = ['NewProject']
  if (planRequired.includes(to.name) && !auth.canCreateProjects) {
    return next('/pricing')
  }

  next()
})

export default router
