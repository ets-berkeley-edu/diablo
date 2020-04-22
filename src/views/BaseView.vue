<template>
  <v-container fluid>
    <v-app-bar
      v-if="!$route.meta.printable"
      app
      color="header-background"
      dark
    >
      <div>
        <h1>Course Capture</h1>
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
    <v-row>
      <v-navigation-drawer
        permanent
        color="nav-background"
        :expand-on-hover="true"
        :mini-variant="true"
        :right="false"
        absolute
        dark
      >
        <v-list
          dense
          nav
          class="py-0"
        >
          <v-list-item two-line class="px-0" @click="toRoute('/')">
            <v-list-item-avatar>
              <img alt="Oski the Bear" src="@/assets/cal.png">
            </v-list-item-avatar>
            <v-list-item-content>
              <v-list-item-title>UC Berkeley</v-list-item-title>
              <v-list-item-subtitle>Course Capture</v-list-item-subtitle>
            </v-list-item-content>
          </v-list-item>
          <v-divider></v-divider>
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
    </v-row>
    <v-row color="body-background" class="ma-3 ml-12 mb-12 pl-4" no-gutters>
      <v-col v-if="loading">
        <div class="text-center ma-12">
          <Spinner />
        </div>
      </v-col>
      <v-col>
        <v-content>
          <router-view :key="$route.fullPath"></router-view>
        </v-content>
      </v-col>
    </v-row>
    <v-row v-if="!loading" no-gutters>
      <v-col>
        <Footer />
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
  import Context from '@/mixins/Context'
  import Footer from '@/components/util/Footer'
  import Spinner from '@/components/util/Spinner'
  import Util from '@/mixins/Utils'
  import {getCasLogoutUrl} from '@/api/auth'

  export default {
    name: 'BaseView',
    components: {Footer, Spinner},
    mixins: [Context, Util],
    data: () => ({
      navItems: undefined,
    }),
    created() {
      if (this.$currentUser.isAdmin) {
        this.navItems = [
          { title: 'Ouija Board', icon: 'mdi-auto-fix', path: '/ouija' },
          { title: 'Rooms', icon: 'mdi-domain', path: '/rooms' },
          { title: 'Course Changes', icon: 'mdi-swap-horizontal', path: '/changes' }
        ]
      } else {
        this.navItems = [
          { title: 'Home', icon: 'mdi-home', path: '/home' }
        ]
        this.$_.each(this.$currentUser.courses, course => {
          if (course.room && course.room.capability) {
            this.navItems.push({
              title: course.label,
              icon: 'mdi-video-plus',
              path: `/approve/${this.$config.currentTermId}/${course.sectionId}`
            })
          }
        })
        this.navItems.push({ title: 'About', icon: 'mdi-help-box' })
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
