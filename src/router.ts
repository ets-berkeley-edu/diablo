import _ from 'lodash'
import auth from './auth'
import Attic from '@/views/Attic.vue'
import BaseView from '@/views/BaseView.vue'
import Course from '@/views/Course.vue'
import CourseChanges from '@/views/CourseChanges.vue'
import EditEmailTemplate from '@/views/email/EditEmailTemplate.vue'
import EmailTemplates from '@/views/email/EmailTemplates.vue'
import Error from '@/views/Error.vue'
import Home from '@/views/Home.vue'
import Jobs from '@/views/Jobs.vue'
import Login from '@/views/Login.vue'
import NotFound from '@/views/NotFound.vue'
import Ouija from '@/views/Ouija.vue'
import PrintableRoom from '@/views/room/PrintableRoom.vue'
import Room from '@/views/room/Room.vue'
import Rooms from '@/views/room/Rooms.vue'
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
      beforeEnter: auth.requiresAdmin,
      path: '/room/printable/:id',
      component: PrintableRoom,
      meta: {
        printable: true,
        title: 'Print Room'
      }
    },
    {
      path: '/login',
      component: Login,
      beforeEnter: (to: any, from: any, next: any) => {
        if (Vue.prototype.$currentUser.isAuthenticated) {
          next('/')
        } else {
          next()
        }
      },
      meta: {
        splash: true,
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
              next({path: '/ouija'})
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
          path: '/course/:termId/:sectionId',
          component: Course
        }
      ]
    },
    {
      path: '/',
      beforeEnter: auth.requiresAdmin,
      component: BaseView,
      children: [
        {
          path: '/attic',
          component: Attic,
          meta: {
            title: 'The Attic'
          }
        },
        {
          path: '/changes',
          component: CourseChanges,
          meta: {
            title: 'Course Changes'
          }
        },
        {
          path: '/email/templates',
          component: EmailTemplates,
          meta: {
            title: 'Email Templates'
          }
        },
        {
          path: '/email/template/create/:type',
          component: EditEmailTemplate,
          meta: {
            title: 'Create Email Template'
          }
        },
        {
          path: '/email/template/edit/:id',
          component: EditEmailTemplate,
          meta: {
            title: 'Edit Email Template'
          }
        },
        {
          path: '/jobs',
          component: Jobs,
          meta: {
            title: 'The Engine Room'
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

router.beforeEach((to: any, from: any, next: any) => {
  const redirect = _.trim(to.query.redirect)
  if (Vue.prototype.$currentUser.isAuthenticated && redirect) {
    next(redirect)
  } else {
    next()
  }
})

router.afterEach((to: any) => {
  const title = _.get(to, 'meta.title') || _.capitalize(to.name) || 'Welcome'
  document.title = `${title} | Course Capture`
})

export default router
