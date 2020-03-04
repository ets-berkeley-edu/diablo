import _ from 'lodash'
import auth from './auth'
import BaseView from '@/views/BaseView.vue'
import Home from '@/views/Home.vue'
import Login from '@/views/Login.vue'
import NotFound from '@/views/NotFound.vue'
import Router from 'vue-router'
import SignUp from '@/views/SignUp.vue'
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
          path: '/course/:section_id',
          component: SignUp
        }
      ]
    },
    {
      path: '/',
      beforeEnter: auth.requiresAdmin,
      component: BaseView,
      children: [
        {
          path: '/home',
          component: Home,
          meta: {
            title: 'Home'
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
