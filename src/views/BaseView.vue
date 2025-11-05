<template>
  <v-app>
    <v-app-bar
      v-if="!route.meta.printable"
      v-wave="waveOptions"
      color="banner"
    >
      <a
        id="skip-to-content-link"
        href="#content"
        class="sr-only sr-only-focusable"
      >
        Skip to main content
      </a>
      <CourseCaptureBanner />
      <v-spacer />
      <v-menu eager>
        <template #activator="{ props }">
          <v-btn
            id="btn-main-menu"
            class="mr-5"
            color="secondary"
            variant="elevated"
            v-bind="props"
          >
            {{ currentUser.firstName || currentUser.lastName || `UID: ${currentUser.uid}` }}
          </v-btn>
        </template>
        <v-list rounded class="pa-2 profile-menu" color="on-surface">
          <v-list-item
            v-if="currentUser.isAdmin"
            id="menu-item-attic"
            component="router-link"
            to="/attic"
          >
            <v-list-item-title>The Attic</v-list-item-title>
          </v-list-item>
          <v-list-item
            id="menu-item-feedback-and-help"
            :href="`mailto:${config.emailCourseCaptureSupport}`"
            target="_blank"
          >
            <v-list-item-title>
              Feedback/Help
            </v-list-item-title>
          </v-list-item>
          <v-list-item id="menu-item-dark-mode" role="button" @click="toggleTheme">
            <v-list-item-title>
              {{ currentUser.prefersDarkMode ? 'Light' : 'Dark' }} mode
            </v-list-item-title>
          </v-list-item>
          <v-list-item id="menu-item-log-out" @click="logOut">
            <v-list-item-title>Log Out</v-list-item-title>
          </v-list-item>
        </v-list>
      </v-menu>
    </v-app-bar>
    <v-navigation-drawer
      v-if="currentUser.courses.length || currentUser.isAdmin"
      v-model="drawer"
      color="tertiary"
      expand-on-hover
      permanent
      rail
      role="navigation"
      class="sidebar-nav"
    >
      <v-list role="none" tabindex="-1">
        <template v-for="(item, i) in navItems" :key="i">
          <v-list-item
            :id="`sidebar-link-${kebabCase(item.title)}`"
            :active="route.path === item.path"
            component="router-link"
            :to="item.path"
            :aria-current="route.path === item.path ? 'page' : false"
            tabindex="0"
            tag="a"
            @click="() => contextStore.broadcast('sidebar-navigation-click', item)"
          >
            <template #prepend>
              <v-icon color="icon-nav" :icon="item.icon" />
            </template>
            <v-list-item-title>
              <span class="text-subtitle-1 text-white">{{ item.title }}</span>
            </v-list-item-title>
          </v-list-item>
          <v-divider
            v-if="item.title === 'Rooms'"
            class="border-opacity-80 ml-1 mr-1"
            color="icon-nav"
            :thickness="1"
          />
        </template>
      </v-list>
    </v-navigation-drawer>

    <v-main id="content" class="ma-3" width="calc(100vw - 38px)">
      <div class="px-md-4 py-md-5">
        <Snackbar />
        <Spinner v-if="loading" />
        <router-view :key="stripAnchorRef(route.fullPath)" />
      </div>
    </v-main>
    <Footer />
  </v-app>
</template>

<script setup>
import {computed, onMounted, ref} from 'vue'
import {kebabCase, noop} from 'lodash'
import {useRoute} from 'vue-router'
import {storeToRefs} from 'pinia'
import {useTheme} from 'vuetify'
import {
  mdiAutoFix,
  mdiDomain,
  mdiEmailOpenMultipleOutline,
  mdiHandsPray,
  mdiHome,
  mdiVideoOffOutline,
  mdiVideoPlus,
} from '@mdi/js'
import CourseCaptureBanner from '@/components/util/CourseCaptureBanner'
import Footer from '@/components/util/Footer'
import Snackbar from '@/components/util/Snackbar'
import Spinner from '@/components/util/Spinner'
import {getCasLogoutUrl} from '@/api/auth'
import {getCourseCodes} from '@/lib/berkeley'
import {putFocusNextTick, stripAnchorRef} from '@/lib/utils'
import {updatePrefersDarkMode} from '@/api/user'
import {useContextStore} from '@/stores/context'

const contextStore = useContextStore()
const {config, currentUser, loading} = storeToRefs(contextStore)
const drawer = ref(true)
const navItems = ref([])
const route = useRoute()
const theme = useTheme()
const waveOptionsDefault = ref({
  cancellationPeriod: 75,
  dissolveDuration: 0.4,
  easing: 'ease-out',
  tagName: 'div',
  trigger: 'auto',
})
const waveOptionsDark = {
  color: 'no-repeat url(../src/assets/bats.png) left center / 50%',
  duration: 4,
  initialOpacity: 1
}
const waveOptionsLight = {
  color: [
    '#1abc9c',
    '#2980b9',
    '#2980b9',
    '#378dc5',
    '#378dc5',
    '#378dc5',
    '#d35400',
    '#f1c40f'
  ][Math.floor(Math.random() * 8)],
  duration: 1.8,
  initialOpacity: 0.2
}

const waveOptions = computed(() => {
  return {
    ...waveOptionsDefault.value,
    ...(theme.global.current.value.dark ? waveOptionsDark : waveOptionsLight)
  }
})

onMounted(() => {
  theme.change(currentUser.value.prefersDarkMode ? 'dark' : 'light')
  navItems.value = currentUser.value.courses.length
    ? [{title: 'Home', icon: mdiHome, path: '/home'}]
    : []
  if (currentUser.value.isAdmin) {
    navItems.value.push(
      {title: 'Ouija Board', icon: mdiAutoFix, path: '/ouija'},
      {title: 'Rooms', icon: mdiDomain, path: '/rooms'},
      {title: 'Blackouts', icon: mdiVideoOffOutline, path: '/blackouts'},
      {
        title: 'Email Templates',
        icon: mdiEmailOpenMultipleOutline,
        path: '/email/templates',
      },
      {title: 'The Chancel', icon: mdiHandsPray, path: '/jobs'}
    )
  } else {
    currentUser.value.courses.forEach((course) => {
      if (course.meetings.eligible.length) {
        navItems.value.push({
          title: getCourseCodes(course)[0],
          icon: mdiVideoPlus,
          path: `/course/${config.value.currentTermId}/${course.sectionId}`,
        })
      }
    })
  }
})

const logOut = () => {
  contextStore.alertScreenReader('Logging out')
  getCasLogoutUrl().then((data) => (window.location.href = data.casLogoutUrl))
}

const toggleTheme = () => {
  const prefersDarkMode = !currentUser.value.prefersDarkMode
  theme.change(prefersDarkMode ? 'dark' : 'light')
  updatePrefersDarkMode(prefersDarkMode).then(noop)
  putFocusNextTick('btn-main-menu')
}
</script>

<style scoped>
:deep(.v-toolbar) {
  left: 0 !important;
  position: fixed !important;
  width: 100% !important;
}
.sidebar-with-banner .v-navigation-drawer__content {
  padding-top: 64px; /* or however tall your banner is */
}
</style>
