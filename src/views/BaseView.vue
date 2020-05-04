<template>
  <v-app :id="$vuetify.theme.dark ? 'dark' : 'light'">
    <v-navigation-drawer
      app
      permanent
      color="nav-background"
      :expand-on-hover="true"
      :mini-variant="true"
      :clipped="$vuetify.breakpoint.lgAndUp"
      :right="false"
      dark
    >
      <v-list nav>
        <v-list-item id="nav-link-home" @click="toRoute('/')">
          <v-list-item-icon class="align-self-center">
            <v-icon color="icon-nav-default">{{ $currentUser.isAdmin ? 'mdi-auto-fix' : 'mdi-home' }}</v-icon>
          </v-list-item-icon>
          <v-list-item-content>
            <v-list-item-title>
              {{ $currentUser.isAdmin ? 'Ouija Board' : 'Home' }}
            </v-list-item-title>
          </v-list-item-content>
        </v-list-item>
        <v-list-item
          v-for="(item, index) in navItems"
          :id="`sidebar-link-${item.title}`"
          :key="index"
          link
          @click="toRoute(item.path)"
        >
          <v-list-item-icon>
            <v-icon color="icon-nav-default">{{ item.icon }}</v-icon>
          </v-list-item-icon>
          <v-list-item-content>
            <v-list-item-title>{{ item.title }}</v-list-item-title>
          </v-list-item-content>
        </v-list-item>
        <v-list-item @click="$vuetify.theme.dark = !$vuetify.theme.dark">
          <v-list-item-icon>
            <v-icon color="icon-nav-default">mdi-lightbulb-outline</v-icon>
          </v-list-item-icon>
          <v-list-item-content>
            <v-list-item-title>{{ $vuetify.theme.dark ? 'Light' : 'Dark' }} mode</v-list-item-title>
          </v-list-item-content>
        </v-list-item>
      </v-list>
    </v-navigation-drawer>
    <v-app-bar
      v-if="!$route.meta.printable"
      app
      :clipped-left="$vuetify.breakpoint.lgAndUp"
      color="header-background"
      dark
    >
      <div class="display-1">
        Course Capture
        <a
          id="skip-to-content-link"
          href="#content"
          class="sr-only sr-only-focusable"
          tabindex="0">
          Skip to main content
        </a>
      </div>
      <v-spacer></v-spacer>
      <v-menu class="mr-2" offset-y>
        <template v-slot:activator="{ on }">
          <v-btn
            id="btn-main-menu"
            color="primary"
            dark
            v-on="on"
          >
            {{ $currentUser.firstName }}
          </v-btn>
        </template>
        <v-list class="pr-2">
          <v-list-item
            id="menu-item-feedback-and-help"
            :href="`mailto:${$config.supportEmailAddress}`"
            target="_blank"
            aria-label="Send email to the Course Capture support team; this link opens a new tab.">
            <v-list-item-title>Feedback/Help</v-list-item-title>
          </v-list-item>
          <v-list-item v-if="$currentUser.isAdmin" id="menu-item-email-templates" @click="goToPath('/email/templates')">
            <v-list-item-title>Email Templates</v-list-item-title>
          </v-list-item>
          <v-list-item v-if="$currentUser.isAdmin" id="menu-item-jobs" @click="goToPath('/jobs')">
            <v-list-item-title>Jobs</v-list-item-title>
          </v-list-item>
          <v-list-item id="menu-item-log-out" @click="logOut">
            <v-list-item-title>Log Out</v-list-item-title>
          </v-list-item>
        </v-list>
      </v-menu>
    </v-app-bar>
    <v-content>
      <div class="ma-3">
        <Snackbar />
        <Spinner v-if="loading" />
        <router-view id="content" :key="$route.fullPath"></router-view>
      </div>
    </v-content>
    <Footer />
  </v-app>
</template>

<script>
  import Context from '@/mixins/Context'
  import Footer from '@/components/util/Footer'
  import Snackbar from '@/components/util/Snackbar'
  import Spinner from '@/components/util/Spinner'
  import Util from '@/mixins/Utils'
  import {getCasLogoutUrl} from '@/api/auth'

  export default {
    name: 'BaseView',
    components: {Footer, Snackbar, Spinner},
    mixins: [Context, Util],
    data: () => ({
      navItems: undefined,
    }),
    created() {
      if (this.$currentUser.isAdmin) {
        this.navItems = [
          { title: 'Rooms', icon: 'mdi-domain', path: '/rooms' },
          { title: 'Course Changes', icon: 'mdi-swap-horizontal', path: '/changes' }
        ]
      } else {
        this.navItems = []
        this.$_.each(this.$currentUser.courses, course => {
          if (course.room && course.room.capability) {
            this.navItems.push({
              title: course.label,
              icon: 'mdi-video-plus',
              path: `/course/${this.$config.currentTermId}/${course.sectionId}`
            })
          }
        })
      }
    },
    methods: {
      logOut: () => getCasLogoutUrl().then(data => window.location.href = data.casLogoutUrl),
      toRoute(path) {
        this.$router.push({ path }, this.$_.noop)
      }
    }
  }
</script>
