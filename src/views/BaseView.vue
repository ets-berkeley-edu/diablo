<template>
  <v-container fluid>
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
            v-for="item in navItems"
            :id="`sidebar-link-${item.title}`"
            :key="item.title"
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
              <v-icon color="icon-nav-dark-mode">mdi-lightbulb</v-icon>
            </v-list-item-icon>
            <v-list-item-content>
              <v-list-item-title class="sr-only">Turn on {{ $vuetify.theme.dark ? 'light' : 'dark' }} mode</v-list-item-title>
            </v-list-item-content>
          </v-list-item>
        </v-list>
      </v-navigation-drawer>
    </v-row>
    <v-row color="body-background" class="ma-3 ml-12 mb-12 pl-4" no-gutters>
      <v-col v-if="loading">
        <div class="text-center ma-12">
          <v-progress-circular
            class="spinner"
            :indeterminate="true"
            rotate="5"
            size="64"
            width="8"
            color="light-blue"
          ></v-progress-circular>
        </div>
      </v-col>
      <v-col v-show="!loading">
        <router-view :key="$route.fullPath"></router-view>
      </v-col>
    </v-row>
    <v-row v-if="!loading" class="ml-8" no-gutters>
      <v-col>
        <Footer />
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
  import Footer from '@/components/util/Footer'
  import Util from '@/mixins/Utils'
  import store from '@/store'
  import {mapGetters} from 'vuex'

  export default {
    name: 'BaseView',
    components: {Footer},
    mixins: [Util],
    data: () => ({
      navItems: undefined,
    }),
    computed: {
      ...mapGetters('context', ['loading'])
    },
    beforeCreate: () => store.dispatch('context/loadingStart'),
    created() {
      if (this.$currentUser.isAdmin) {
        this.navItems = [
          { title: 'Ouija Board', icon: 'mdi-auto-fix', path: '/ouija' },
          { title: 'Rooms', icon: 'mdi-domain', path: '/rooms' },
          { title: 'Course Changes', icon: 'swap-horizontal', path: '/changes' },
          { title: 'About', icon: 'mdi-help-box' }
        ]
      } else {
        this.navItems = [
          { title: 'Home', icon: 'mdi-home', path: '/home' }
        ]
        this.$_.each(this.organizeMySections().eligibleOnly, eligible => {
          this.navItems.push({ title: eligible.name, icon: 'mdi-video-plus', path: `/approve/${this.$config.currentTermId}/${eligible.sectionId}` })
        })
        this.navItems.push({ title: 'About', icon: 'mdi-help-box' })
      }
    },
    methods: {
      toRoute(path) {
        this.$router.push({ path }, this.$_.noop)
      }
    }
  }
</script>

<style scoped>
.spinner {
  position: fixed;
  top: 0;
  right: 0;
  bottom: 0;
  left: 0;
  height: 2em;
  margin: auto;
  overflow: show;
  width: 2em;
  z-index: 999;
}
</style>
