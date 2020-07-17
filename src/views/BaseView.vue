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
          tabindex="0"
        >
          Skip to main content
        </a>
      </div>
      <v-spacer></v-spacer>
      <v-menu offset-y rounded="lg">
        <template v-slot:activator="{ on, attrs }">
          <v-btn
            id="btn-main-menu"
            v-bind="attrs"
            color="primary"
            dark
            v-on="on"
          >
            {{ $currentUser.firstName }}
          </v-btn>
        </template>
        <v-list>
          <v-list-item
            id="menu-item-feedback-and-help"
            aria-label="Send email to the Course Capture support team; this link opens a new tab."
            :href="`mailto:${$config.emailCourseCaptureSupport}`"
            link
            target="_blank"
          >
            <v-list-item-content>Feedback/Help</v-list-item-content>
          </v-list-item>
          <v-list-item
            v-if="$currentUser.isAdmin"
            id="menu-item-email-templates"
            link
            @click="goToPath('/email/templates')"
          >
            <v-list-item-content>Email Templates</v-list-item-content>
          </v-list-item>
          <v-list-item
            v-if="$currentUser.isAdmin"
            id="menu-item-jobs"
            link
            @click="goToPath('/jobs')"
          >
            <v-list-item-content>Jobs</v-list-item-content>
          </v-list-item>
          <v-list-item id="menu-item-log-out" link @click="logOut">
            <v-list-item-content>Log Out</v-list-item-content>
          </v-list-item>
        </v-list>
      </v-menu>
    </v-app-bar>
    <v-main id="content" class="ma-3">
      <Snackbar />
      <Spinner v-if="loading" />
      <router-view :key="stripAnchorRef($route.fullPath)"></router-view>
    </v-main>
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
      this.prefersColorScheme()
      this.navItems = this.$currentUser.courses.length ? [{ title: 'Home', icon: 'mdi-home', path: '/home' }] : []
      if (this.$currentUser.isAdmin) {
        this.navItems = this.navItems.concat([
          { title: 'Ouija Board', icon: 'mdi-auto-fix', path: '/ouija' },
          { title: 'Rooms', icon: 'mdi-domain', path: '/rooms' },
          { title: 'Course Changes', icon: 'mdi-directions-fork', path: '/changes' },
          { title: 'The Attic', icon: 'mdi-candle', path: '/attic' }
        ])
      } else {
        this.$_.each(this.$currentUser.courses, course => {
          if (course.meetings.eligible.length) {
            this.navItems.push({
              title: this.getCourseCodes(course)[0],
              icon: 'mdi-video-plus',
              path: `/course/${this.$config.currentTermId}/${course.sectionId}`
            })
          }
        })
      }
    },
    methods: {
      logOut() {
        this.alertScreenReader('Logging out')
        getCasLogoutUrl().then(data => window.location.href = data.casLogoutUrl)
      },
      prefersColorScheme() {
        const mq = window.matchMedia('(prefers-color-scheme: dark)')
        this.$vuetify.theme.dark = mq.matches
        if (typeof mq.addEventListener === 'function') {
          mq.addEventListener('change', e => this.$vuetify.theme.dark = e.matches)
        }
      },
      toRoute(path) {
        this.$router.push({ path }, this.$_.noop)
      }
    }
  }
</script>
