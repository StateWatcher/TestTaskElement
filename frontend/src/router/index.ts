/** Маршруты и guard админки.
 *
 * Экраны грузятся лениво: помимо размера бандла это разрывает цикл импортов
 * router → views → lib/notify → router (notify редиректит на логин по 401).
 */

import { createRouter, createWebHistory } from 'vue-router'

import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', redirect: { name: 'lots' } },
    {
      path: '/lots',
      name: 'lots',
      component: () => import('@/views/public/LotListView.vue'),
    },
    {
      path: '/lots/:id',
      name: 'lot',
      component: () => import('@/views/public/LotDetailView.vue'),
      props: (route) => ({ id: Number(route.params.id) }),
    },
    {
      path: '/admin/login',
      name: 'login',
      component: () => import('@/views/admin/LoginView.vue'),
    },
    { path: '/admin', redirect: { name: 'admin-sets' } },
    {
      path: '/admin/sets',
      name: 'admin-sets',
      component: () => import('@/views/admin/SetsView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/admin/bookings',
      name: 'admin-bookings',
      component: () => import('@/views/admin/BookingsView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/admin/requests',
      name: 'admin-requests',
      component: () => import('@/views/admin/ApplicationsView.vue'),
      meta: { requiresAuth: true },
    },
  ],
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()

  if (to.meta.requiresAuth && !(await auth.ensureSession())) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  // на логин с живой сессией ходить незачем
  if (to.name === 'login' && (await auth.ensureSession())) {
    return { name: 'admin-sets' }
  }
  return true
})

export default router
