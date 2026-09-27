import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useAdminAuthStore } from '@/stores/adminAuth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    // 学生端登录
    { path: '/login', component: () => import('@/apps/student/views/LoginView.vue') },

    // 学生端
    {
      path: '/',
      component: () => import('@/apps/student/StudentLayout.vue'),
      meta: { requiresAuth: true, app: 'student' },
      children: [
        { path: '', redirect: '/subjects' },
        { path: 'subjects', component: () => import('@/apps/student/views/SubjectsView.vue') },
        { path: 'subject/:subjectId', component: () => import('@/apps/student/views/SubjectDetailView.vue') },
        { path: 'camera/:subjectId', component: () => import('@/apps/student/views/CameraView.vue') },
        { path: 'result/:recordId', component: () => import('@/apps/student/views/ResultView.vue') },
        { path: 'mistakes', component: () => import('@/apps/student/views/MistakesView.vue') },
        { path: 'profile', component: () => import('@/apps/student/views/ProfileView.vue') },
      ]
    },

    // 后台管理登录
    { path: '/mgmt/login', component: () => import('@/apps/admin/views/AdminLoginView.vue') },

    // 后台管理
    {
      path: '/mgmt',
      component: () => import('@/apps/admin/AdminLayout.vue'),
      meta: { requiresAuth: true, app: 'admin' },
      children: [
        { path: '', redirect: '/mgmt/dashboard' },
        { path: 'dashboard', component: () => import('@/apps/admin/views/DashboardView.vue') },
        { path: 'users', component: () => import('@/apps/admin/views/UsersView.vue') },
        { path: 'llm', component: () => import('@/apps/admin/views/LLMView.vue') },
        { path: 'exercise-types', component: () => import('@/apps/admin/views/ExerciseTypesView.vue') },
        { path: 'exercise-types/:typeId', component: () => import('@/apps/admin/views/ExerciseTypeDetailView.vue') },
        { path: 'general-prompts', component: () => import('@/apps/admin/views/GeneralPromptsView.vue') },
      ]
    },

    { path: '/:pathMatch(.*)*', redirect: '/' }
  ]
})

// 路由守卫
router.beforeEach((to) => {
  if (to.meta.app === 'admin') {
    const adminAuth = useAdminAuthStore()
    if (!adminAuth.isLoggedIn) return '/mgmt/login'
    if (!adminAuth.isAdmin) return '/mgmt/login'
  } else if (to.meta.app === 'student') {
    const auth = useAuthStore()
    if (!auth.isLoggedIn) return '/login'
  }

  if (to.path === '/login') {
    const auth = useAuthStore()
    if (auth.isLoggedIn) return '/subjects'
  }
  if (to.path === '/mgmt/login') {
    const adminAuth = useAdminAuthStore()
    if (adminAuth.isLoggedIn && adminAuth.isAdmin) return '/mgmt/dashboard'
  }
})

export default router
