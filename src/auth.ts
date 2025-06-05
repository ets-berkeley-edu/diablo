import type {
  NavigationGuard,
  NavigationGuardNext,
  RouteLocationNormalized,
} from 'vue-router'
import {useContextStore} from '@/stores/context'

const goToLogin = (
  to: RouteLocationNormalized,
  next: NavigationGuardNext
) => {
  next({
    path: '/login',
    query: {
      error: to.query.error as string | undefined,
      redirect: to.name === 'home' ? undefined : to.fullPath,
    },
  })
}

export const requiresAdmin: NavigationGuard = (to, from, next) => {
  const {isAuthenticated, isAdmin} = useContextStore().currentUser
  if (!isAuthenticated) {
    return goToLogin(to, next)
  }

  return isAdmin
    ? next()
    : next({path: '/404'})
}

export const requiresInstructor: NavigationGuard = (to, from, next) => {
  const {isTeaching, isAdmin} = useContextStore().currentUser
  return isTeaching || isAdmin
    ? next()
    : goToLogin(to, next)
}
