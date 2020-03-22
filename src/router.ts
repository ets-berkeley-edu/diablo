import _ from 'lodash'
import Approve from '@/views/Approve.vue'
import Attic from '@/views/Attic.vue'
import auth from './auth'
import BaseView from '@/views/BaseView.vue'
import CourseChanges from '@/views/CourseChanges.vue'
import Error from '@/views/Error.vue'
import Home from '@/views/Home.vue'
import Login from '@/views/Login.vue'
import NotFound from '@/views/NotFound.vue'
import Ouija from '@/views/Ouija.vue'
import Room from '@/views/Room.vue'
import Rooms from '@/views/Rooms.vue'
import User from '@/views/User.vue'
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
              next({ path: '/ouija' })
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
          path: '/changes',
          component: CourseChanges,
          meta: {
            title: 'Course Changes'
          }
        },
        {
          path: '/ouija',
          component: Ouija,
          meta: {
            title: 'The Ouija Board'
          }
        },
        {
          path: '/room/:id',
          component: Room,
          meta: {
            title: 'Room'
          }
        },
        {
          path: '/rooms',
          component: Rooms,
          meta: {
            title: 'Rooms'
          }
        },
        {
          path: '/user/:uid',
          component: User,
          meta: {
            title: 'User'
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
          path: '/error',
          component: Error,
          meta: {
            title: 'Error'
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
