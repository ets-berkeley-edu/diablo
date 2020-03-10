import _ from 'lodash'
import Approve from '@/views/Approve.vue'
import Attic from '@/views/Attic.vue'
import auth from './auth'
import BaseView from '@/views/BaseView.vue'
import Home from '@/views/Home.vue'
import Login from '@/views/Login.vue'
import NotFound from '@/views/NotFound.vue'
import Reports from '@/views/Reports.vue'
import Router from 'vue-router'
import Vue from 'vue'

Vue.use(Router)

const router = new Router({
  mode: 'history',
  routes: [
    {
      path: '/',
      redirect: '/home'
    },
    {
      path: '/login',
      component: Login,
      beforeEnter: (to: any, from: any, next: any) => {
        const currentUser = Vue.prototype.$currentUser
        if (currentUser.isAuthenticated) {
          if (_.trim(to.query.redirect)) {
            next(to.query.redirect)
          } else {
            next('/home')
          }
        } else {
          next()
        }
      },
      meta: {
        title: 'Welcome'
      }
    },
    {
      path: '/',
      component: BaseView,
      beforeEnter: auth.requiresInstructor,
      children: [
        {
          beforeEnter: (to: any, from: any, next: any) => {
            const currentUser = Vue.prototype.$currentUser
            if (currentUser.isAdmin && !currentUser.isTeaching) {
              next({ path: '/reports' })
            } else {
              next()
            }
          },
          path: '/home',
          component: Home,
          meta: {
            title: 'Home'
          },
          name: 'home'
        },
        {
          path: '/approve/:termId/:sectionId',
          component: Approve
        },
        {
          path: '/attic',
          component: Attic,
          meta: {
            title: 'The Attic'
          }
        }
      ]
    },
    {
      path: '/',
      beforeEnter: auth.requiresAdmin,
      component: BaseView,
      children: [
        {
          path: '/reports',
          component: Reports,
          meta: {
            title: 'Reports'
          }
        }
      ]
    },
    {
      path: '/',
      component: BaseView,
      children: [
        {
          path: '/404',
          component: NotFound,
          meta: {
            title: 'Page not found'
          }
        },
        {
          path: '*',
          redirect: '/404'
        }
      ]
    }
  ]
})

router.afterEach((to: any) => {
  const title = _.get(to, 'meta.title') || _.capitalize(to.name) || 'Welcome'
  document.title = `${title} | Diablo`
})

export default router
