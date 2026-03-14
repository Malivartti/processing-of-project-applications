import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/projects' },
    { path: '/projects', component: () => import('../views/ProjectsView.vue') },
    { path: '/selection', component: () => import('../views/SelectionView.vue') },
    { path: '/history', component: () => import('../views/HistoryView.vue') },
    { path: '/dictionaries', component: () => import('../views/DictionariesView.vue') },
  ],
})

export default router
