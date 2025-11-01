import { createRouter, createWebHistory } from 'vue-router';

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'dashboard',
      component: () => import('../components/Dashboard.vue'),
    },
    {
      path: '/registration',
      name: 'registration',
      component: () => import('../components/Registration.vue'),
    },
    {
      path: '/dns',
      name: 'dns',
      component: () => import('../components/DNS.vue'),
    },
    {
      path: '/dnssec',
      name: 'dnssec',
      component: () => import('../components/DNSSEC.vue'),
    },
    {
      path: '/certificate',
      name: 'certificate',
      component: () => import('../components/Certificate.vue'),
    },
    {
      path: '/http',
      name: 'http',
      component: () => import('../components/HTTP.vue'),
    },
    {
      path: '/email',
      name: 'email',
      component: () => import('../components/Email.vue'),
    },
  ],
});

export default router;
