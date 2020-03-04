import Vue from 'vue'

const $_goToLogin = (to: any, next: any) => {
  next({
    path: '/login',
    query: {
      error: to.query.error,
      redirect: to.name === 'home' ? undefined : to.fullPath
    }
  })
}

export default {
  requiresAdmin: (to: any, from: any, next: any) => {
    const currentUser = Vue.prototype.$currentUser
    if (currentUser.isAuthenticated) {
      if (currentUser.isAdmin) {
        next()
      } else {
        next({ path: '/404' })
      }
    } else {
      $_goToLogin(to, next)
    }
  },
  requiresInstructor: (to: any, from: any, next: any) => {
    const currentUser = Vue.prototype.$currentUser
    if (currentUser.isTeaching || currentUser.isAdmin) {
      next()
    } else {
      $_goToLogin(to, next)
    }
  }
}
