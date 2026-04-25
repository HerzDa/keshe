import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '../views/LoginView.vue'
import DashboardView from '../views/DashboardView.vue'
import InvoiceView from '../views/InvoiceView.vue'
import ReimbursementView from '../views/ReimbursementView.vue'
import HistoryView from '../views/HistoryView.vue'
import BudgetView from '../views/BudgetView.vue'
import StatisticsView from '../views/StatisticsView.vue'
import AccountantReviewView from '../views/AccountantReviewView.vue'

const routes = [
  { path: '/', redirect: '/login' },
  { path: '/login', component: LoginView },
  { path: '/dashboard', component: DashboardView },
  { path: '/invoice', component: InvoiceView },
  { path: '/reimbursement', component: ReimbursementView },
  { path: '/history', component: HistoryView },
  { path: '/budget', component: BudgetView },
  { path: '/statistics', component: StatisticsView },
  { path: '/accountant', component: AccountantReviewView }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, _from, next) => {
  const publicPaths = ['/login']
  const user = localStorage.getItem('user')
  if (!publicPaths.includes(to.path) && !user) {
    next('/login')
  } else {
    next()
  }
})

export default router
