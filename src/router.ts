import {createRouter, createWebHistory, NavigationGuardNext, RouteLocationNormalized} from 'vue-router'
import {get, toString, trim} from 'lodash'
import {useContextStore} from '@/stores/context'
import {requiresAdmin, requiresInstructor} from '@/auth'
import Attic from '@/views/Attic.vue'
import BaseView from '@/views/BaseView.vue'
import Blackouts from '@/views/blackout/Blackouts.vue'
import EditEmailTemplate from '@/views/email/EditEmailTemplate.vue'
import EmailTemplates from '@/views/email/EmailTemplates.vue'
import ErrorView from '@/views/Error.vue'
import Home from '@/views/Home.vue'
import Jobs from '@/views/Jobs.vue'
import Login from '@/views/Login.vue'
import NotFound from '@/views/NotFound.vue'
import Ouija from '@/views/Ouija.vue'
import Room from '@/views/room/Room.vue'
import Rooms from '@/views/room/Rooms.vue'
import Course from '@/views/Course.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/home'
    },
    // {
    //   path: '/room/printable/:id',
    //   component: PrintableRoom,
    //   beforeEnter: requiresAdmin,
    //   meta: {
    //     printable: true,
    //   },
    //   name: 'Print Room'
    // },
    {
      path: '/login',
      component: Login,
      beforeEnter: (to, from, next) => {
        const store = useContextStore()
        store.currentUser.isAuthenticated
          ? next('/')
          : next()
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
            isAdmin && !isTeaching
              ? next({path: '/ouija'})
              : next()
          }
        },
        {
          path: '/course/:termId/:sectionId',
          component: Course
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
      //   {
      //     path: '/user/:uid',
      //     component: User,
      //     name: 'User'
      //   }
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
    isAuthenticated && redirect
      ? next(redirect)
      : next()
  }
)

router.afterEach((to) => {
  const pageTitle = get(to, 'name')
  document.title = `${pageTitle ? toString(pageTitle) : 'Welcome'} | Course Capture`
})

export default router
