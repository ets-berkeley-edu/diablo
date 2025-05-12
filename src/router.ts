import {createRouter, createWebHistory, NavigationGuardNext, RouteLocationNormalized} from 'vue-router'
import _ from 'lodash'
import {useContextStore} from '@/stores/context'
import {requiresAdmin, requiresInstructor} from '@/auth'
import BaseView from '@/views/BaseView.vue'
import ErrorView from '@/views/Error.vue'
import Home from '@/views/Home.vue'
import Login from '@/views/Login.vue'
import NotFound from '@/views/NotFound.vue'
import Ouija from '@/views/Ouija.vue'

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
    //     title: 'Print Room'
    //   }
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
        title: 'Welcome'
      }
    },
    {
      path: '/',
      component: BaseView,
      beforeEnter: requiresInstructor,
      children: [
        {
          path: '/home',
          name: 'home',
          component: Home,
          beforeEnter: (to, from, next) => {
            const {isAdmin, isTeaching} = useContextStore().currentUser
            isAdmin && !isTeaching
              ? next({path: '/ouija'})
              : next()
          },
          meta: {
            title: 'Home'
          }
        },
        // {
        //   path: '/course/:termId/:sectionId',
        //   component: Course
        // }
      ]
    },
    {
      path: '/',
      component: BaseView,
      beforeEnter: requiresAdmin,
      children: [
      //   {
      //     path: '/attic',
      //     component: Attic,
      //     meta: {
      //       title: 'The Attic'
      //     }
      //   },
      //   {
      //     path: '/blackouts',
      //     component: Blackouts,
      //     meta: {
      //       title: 'Blackouts'
      //     }
      //   },
      //   {
      //     path: '/email/templates',
      //     component: EmailTemplates,
      //     meta: {
      //       title: 'Email Templates'
      //     }
      //   },
      //   {
      //     path: '/email/template/create/:type',
      //     component: EditEmailTemplate,
      //     meta: {
      //       title: 'Create Email Template'
      //     }
      //   },
      //   {
      //     path: '/email/template/edit/:id',
      //     component: EditEmailTemplate,
      //     meta: {
      //       title: 'Edit Email Template'
      //     }
      //   },
      //   {
      //     path: '/jobs',
      //     component: Jobs,
      //     meta: {
      //       title: 'The Chancel'
      //     }
      //   },
        {
          path: '/ouija',
          component: Ouija,
          meta: {
            title: 'The Ouija Board'
          }
        },
      //   {
      //     path: '/room/:id',
      //     component: Room,
      //     meta: {
      //       title: 'Room'
      //     }
      //   },
      //   {
      //     path: '/rooms',
      //     component: Rooms,
      //     meta: {
      //       title: 'Rooms'
      //     }
      //   },
      //   {
      //     path: '/user/:uid',
      //     component: User,
      //     meta: {
      //       title: 'User'
      //     }
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
          meta: {
            title: 'Page not found'
          }
        },
        {
          path: '/error',
          component: ErrorView,
          meta: {
            title: 'Error'
          }
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
    const redirect = _.trim(
      (to.query.redirect as string) || ''
    )
    const {isAuthenticated} = useContextStore().currentUser
    isAuthenticated && redirect
      ? next(redirect)
      : next()
  }
)

router.afterEach((to) => {
  const title =
    (to.meta.title as string) ||
    _.capitalize(to.name as string) ||
    'Welcome'
  document.title = `${title} | Course Capture`
})

export default router
