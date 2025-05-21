<template>
  <v-app>
    <v-navigation-drawer
      v-model="drawer"
      color="tertiary"
      expand-on-hover
      permanent
      rail
      role="navigation"
      class="sidebar-nav"
    >
      <v-list>
        <template v-for="(item, i) in navItems" :key="i">
          <v-list-item
            :id="`sidebar-link-${kebabCase(item.title)}`"
            :active="route.path === item.path"
            component="router-link"
            :to="item.path"
            :aria-current="route.path === item.path"
            tag="a"
          >
            <template #prepend>
              <v-icon :icon="item.icon" color="white" />
            </template>
            <v-list-item-title>
              <span class="text-subtitle-1 text-white">{{ item.title }}</span>
            </v-list-item-title>
          </v-list-item>
          <v-divider
            v-if="item.title === 'Rooms'"
            class="border-opacity-80 ml-1 mr-1"
            color="white"
            :thickness="1"
          />
        </template>
      </v-list>
    </v-navigation-drawer>

    <v-app-bar
      v-if="!route.meta.printable"
      color="header-background"
      app
      v-wave="waveOptions"
    >
      <div
        class="display-1 not-selectable banner-overlay"
        :class="{ 'mood-ring': theme.global.current.value.dark }"
      >
        <CourseCaptureBanner />
        <a
          id="skip-to-content-link"
          href="#content"
          class="sr-only sr-only-focusable"
          tabindex="0"
        >
          Skip to main content
        </a>
      </div>

      <v-spacer />

      <v-menu offset-y>
        <template #activator="{ props }">
          <v-btn
            id="btn-main-menu"
            class="mr-5"
            color="secondary"
            variant="elevated"
            v-bind="props"
          >
            {{ currentUser.firstName }}
          </v-btn>
        </template>
        <v-list rounded class="pa-2 profile-menu" color="on-surface">
          <v-list-item
            v-if="currentUser.isAdmin"
            id="menu-item-attic"
            class="text-on-surface"
            color="on-surface"
            component="router-link"
            to="/attic"
          >
            <v-list-item-title class="text-on-surface">The Attic</v-list-item-title>
          </v-list-item>

          <v-list-item
            id="menu-item-feedback-and-help"
            href="mailto:{{ config.emailCourseCaptureSupport }}"
            target="_blank"
          >
            <v-list-item-title>
              Feedback/Help
            </v-list-item-title>
          </v-list-item>

          <v-list-item id="menu-item-dark-mode" @click="toggleTheme">
            <v-list-item-title>
              {{ theme.global.current.value.dark ? 'Light' : 'Dark' }} mode
            </v-list-item-title>
          </v-list-item>

          <v-list-item id="menu-item-log-out" @click="logOut">
            <v-list-item-title>Log Out</v-list-item-title>
          </v-list-item>
        </v-list>
      </v-menu>
    </v-app-bar>
    <v-main id="content" class="ma-3" width="calc(100vw - 38px)">
      <Snackbar />
      <Spinner v-if="loading" />
      <router-view :key="stripAnchorRef(route.fullPath)" />
    </v-main>

    <Footer />
  </v-app>
</template>

<script setup>
import {ref, onMounted} from 'vue'
import {useRouter, useRoute} from 'vue-router'
import {storeToRefs} from 'pinia'
import {useTheme} from 'vuetify'
import {kebabCase} from 'lodash'
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
import {stripAnchorRef, getCourseCodes} from '@/lib/utils'
import {useContextStore} from '@/stores/context'

const contextStore = useContextStore()
const {config, currentUser, loading} = storeToRefs(contextStore)

const drawer = ref(true)
const navItems = ref([])
const route = useRoute()
const router = useRouter()
const theme = useTheme()

const waveOptions = {
  cancellationPeriod: 75,
  color:
    [
      '#1abc9c',
      '#2980b9',
      '#2980b9',
      '#378dc5',
      '#378dc5',
      '#378dc5',
      '#d35400',
      '#f1c40f',
    ][Math.floor(Math.random() * 8)],
  dissolveDuration: 0.4,
  duration: 1.8,
  easing: 'ease-out',
  finalOpacity: 0.1,
  initialOpacity: 0.2,
  tagName: 'div',
  trigger: 'auto',
}

onMounted(() => {
  prefersColorScheme()
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

const prefersColorScheme = () => {
  const mq = window.matchMedia('(prefers-color-scheme: dark)')
  const setColorScheme = (dark) => {
    theme.global.name.value = dark ? 'dark' : 'light'
  }
  setColorScheme(mq.matches)
  mq.addEventListener?.('change', (e) => setColorScheme(e.matches))
}

const toggleTheme = () => {
  theme.global.name.value = theme.global.current.value.dark
    ? 'light'
    : 'dark'
}
</script>

<style>
.sidebar-nav .v-list-item[aria-current="true"]:not(:focus)::before {
  opacity: 0.1;
}
</style>

<style scoped>
::v-deep .v-toolbar {
  left: 0 !important;
  width: 100% !important;
}
::v-deep .v-navigation-drawer {
  top: 63px !important;
}
.sidebar-with-banner .v-navigation-drawer__content {
  padding-top: 64px; /* or however tall your banner is */
}
.mood-ring {
  -webkit-animation: colorchange 300s infinite alternate;
  animation: colorchange 300s infinite alternate;
}
.nav-list-item {
  color: var(--v-icon-nav-default) !important;
}
@-webkit-keyframes colorchange {
  0% {
    color: white;
  }
  10% {
    color: #378dc5;
  }
  20% {
    color: #1abc9c;
  }
  30% {
    color: #d35400;
  }
  40% {
    color: #378dc5;
  }
  50% {
    color: white;
  }
  60% {
    color: #378dc5;
  }
  70% {
    color: #2980b9;
  }
  80% {
    color: #f1c40f;
  }
  90% {
    color: #2980b9;
  }
  100% {
    color: pink;
  }
}
@keyframes colorchange {
  0% {
    color: white;
  }
  10% {
    color: #378dc5;
  }
  20% {
    color: #1abc9c;
  }
  30% {
    color: #d35400;
  }
  40% {
    color: #378dc5;
  }
  50% {
    color: white;
  }
  60% {
    color: #378dc5;
  }
  70% {
    color: #2980b9;
  }
  80% {
    color: #f1c40f;
  }
  90% {
    color: #2980b9;
  }
  100% {
    color: pink;
  }
}
</style>
