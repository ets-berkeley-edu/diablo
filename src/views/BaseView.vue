<template>
  <v-container fluid>
    <v-row>
      <v-navigation-drawer
        permanent
        color="light-blue"
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
              <v-icon>{{ item.icon }}</v-icon>
            </v-list-item-icon>
            <v-list-item-content>
              <v-list-item-title>{{ item.title }}</v-list-item-title>
            </v-list-item-content>
          </v-list-item>
        </v-list>
      </v-navigation-drawer>
    </v-row>
    <v-row class="ma-3 ml-12 pb-12 pl-4" no-gutters>
      <v-col>
        <router-view :key="$route.fullPath"></router-view>
      </v-col>
    </v-row>
    <v-row class="ml-8" no-gutters>
      <v-col class="pt-8">
        <Footer />
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
  import Footer from '@/components/util/Footer'
  import Util from '@/mixins/Utils'

  export default {
    name: 'BaseView',
    components: {Footer},
    mixins: [Util],
    data: () => ({
      drawer: true,
      navItems: undefined,
    }),
    created() {
      if (this.$currentUser.isAdmin) {
        this.navItems = [
          { title: 'Ouija Board', icon: 'mdi-auto-fix', path: '/ouija' },
          { title: 'Rooms', icon: 'mdi-domain', path: '/rooms' },
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
