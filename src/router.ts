// Lazy-loaded view components
const Attic = () => import('@/views/Attic.vue')
const BaseView = () => import('@/views/BaseView.vue')
const Blackouts = () => import('@/views/blackout/Blackouts.vue')
const Course = () => import('@/views/Course.vue')
const EditEmailTemplate = () => import('@/views/email/EditEmailTemplate.vue')
const EmailTemplates = () => import('@/views/email/EmailTemplates.vue')
const ErrorView = () => import('@/views/Error.vue')
const Home = () => import('@/views/Home.vue')
const Jobs = () => import('@/views/Jobs.vue')
const Login = () => import('@/views/Login.vue')
const NotFound = () => import('@/views/NotFound.vue')
const Ouija = () => import('@/views/Ouija.vue')
const Room = () => import('@/views/room/Room.vue')
const Rooms = () => import('@/views/room/Rooms.vue')
const User = () => import('@/views/User.vue')
const PrintableRoom = () => import('@/views/room/PrintableRoom.vue')

import type {NavigationGuardNext, RouteLocationNormalized} from 'vue-router'
import {createRouter, createWebHistory} from 'vue-router'
import {trim} from 'lodash'
import {useContextStore} from '@/stores/context'
import {requiresAdmin, requiresInstructor} from '@/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/home'
    },
    {
      path: '/room/printable/:id',
      component: PrintableRoom,
      beforeEnter: requiresAdmin,
      meta: {
        printable: true,
      },
      name: 'Print Room'
    },
    {
      path: '/login',
      component: Login,
      beforeEnter: (to, from, next) => {
        const store = useContextStore()
        if (store.currentUser.isAuthenticated) {
          next('/')
        } else {
          next()
        }
      },
      meta: {
        splash: true,
      },
      name: 'Welcome'
    },
    {
      path: '/',
      component: BaseView,
      beforeEnter: requiresInstructor,
      children: [
        {
          path: '/home',
          name: 'Home',
          component: Home,
          beforeEnter: (to, from, next) => {
            const {isAdmin, isTeaching} = useContextStore().currentUser
            if (isAdmin && !isTeaching) {
              next({path: '/ouija'})
            } else {
              next()
            }
          }
        },
        {
          path: '/course/:termId/:sectionId',
          component: Course,
        }
      ]
    },
    {
      path: '/',
      component: BaseView,
      beforeEnter: requiresAdmin,
      children: [
        {
          path: '/attic',
          component: Attic,
          name: 'The Attic'
        },
        {
          path: '/blackouts',
          component: Blackouts,
          name: 'Blackouts'
        },
        {
          path: '/email/templates',
          component: EmailTemplates,
          name: 'Email Templates'
        },
        {
          path: '/email/template/create/:type',
          component: EditEmailTemplate,
          name: 'Create Email Template'
        },
        {
          path: '/email/template/edit/:id',
          component: EditEmailTemplate,
          name: 'Edit Email Template'
        },
        {
          path: '/jobs',
          component: Jobs,
          name: 'The Chancel'
        },
        {
          path: '/ouija',
          component: Ouija,
          name: 'The Ouija Board'
        },
        {
          path: '/room/:id',
          component: Room,
          name: 'Room'
        },
        {
          path: '/rooms',
          component: Rooms,
          name: 'Rooms'
        },
        {
          path: '/user/:uid',
          component: User,
          name: 'User'
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
          name: 'Page not found'
        },
        {
          path: '/error',
          component: ErrorView,
          name: 'Error'
        },
        {
          path: '/:pathMatch(.*)*',
          redirect: '/404'
        }
      ]
    }
  ]
})

router.beforeEach(
  (
    to: RouteLocationNormalized,
    from: RouteLocationNormalized,
    next: NavigationGuardNext
  ) => {
    const redirect = trim(
      (to.query.redirect as string) || ''
    )
    const {isAuthenticated} = useContextStore().currentUser
    if (isAuthenticated && redirect) {
      next(redirect)
    } else {
      next()
    }
  }
)

export default router
