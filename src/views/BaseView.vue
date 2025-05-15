<template>
  <v-layout>
    <!--          :clipped="$vuetify.breakpoint.lgAndUp"-->
    <v-navigation-drawer
      color="tertiary"
      :expand-on-hover="true"
      permanent
      rail
      role="navigation"
      theme="dark"
    >
      <v-list-item
        v-for="(item, index) in navItems"
        :id="`sidebar-link-${kebabCase(item.title)}`"
        :key="`sidebar-link-${index}`"
        :aria-current="route.path === item.path"
        class="nav-list-item"
        link
        tag="a"
        @click="router.push(item.path)"
      >
        <template #prepend>
          <v-icon color="icon-nav-default" :icon="item.icon" />
        </template>
        <v-list-item-title>
          <span class="font-size-16">{{ item.title }}</span>
        </v-list-item-title>
      </v-list-item>
      <!--  <v-divider v-if="item.title === 'Rooms'" :key="`sidebar-divider-${index}`" />-->
    </v-navigation-drawer>
    <!-- :clipped-left="$vuetify.breakpoint.lgAndUp" -->
    <v-app-bar
      v-if="!route.meta.printable"
      v-wave="waveOptions"
      app
      color="header-background"
      theme="dark"
    >
      <div class="display-1 not-selectable" :class="{'mood-ring': $vuetify.theme.dark}">
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
      <v-spacer></v-spacer>
      <v-menu offset-y rounded="lg">
        <template #activator="{props}">
          <v-btn
            id="btn-main-menu"
            color="secondary"
            theme="dark"
            v-bind="props"
          >
            {{ currentUser.firstName }}
          </v-btn>
        </template>
        <v-list>
          <v-list-item
            v-if="currentUser.isAdmin"
            id="menu-item-attic"
            link
            @click="router.push('/attic')"
          >
            <v-list-item-title>The Attic</v-list-item-title>
          </v-list-item>
          <v-list-item
            id="menu-item-feedback-and-help"
            aria-label="Send email to the Course Capture support team; this link opens a new tab."
            :href="`mailto:${config.emailCourseCaptureSupport}`"
            link
            target="_blank"
          >
            <v-list-item-title class="black--text">Feedback/Help</v-list-item-title>
          </v-list-item>
          <v-list-item id="menu-item-dark-mode" @click="toggleTheme">
            <v-list-item-title>{{ theme.global.current.value.dark ? 'Light' : 'Dark' }} mode</v-list-item-title>
          </v-list-item>
          <v-list-item id="menu-item-log-out" link @click="logOut">
            <v-list-item-title>Log Out</v-list-item-title>
          </v-list-item>
        </v-list>
      </v-menu>
    </v-app-bar>
    <v-main id="content" class="ma-3" width="calc(100vw - 38px)">
      <Snackbar />
      <Spinner v-if="loading" />
      <router-view :key="stripAnchorRef(route.fullPath)"></router-view>
    </v-main>
    <Footer />
  </v-layout>
</template>

<script setup>
import {each, kebabCase} from 'lodash'
import {mdiAutoFix, mdiDomain, mdiEmailOpenMultipleOutline, mdiHandsPray, mdiHome, mdiVideoOffOutline, mdiVideoPlus} from '@mdi/js'
import {onMounted, ref} from 'vue'
import {storeToRefs} from 'pinia'
import {useRoute, useRouter} from 'vue-router'
import {useTheme} from 'vuetify'
import CourseCaptureBanner from '@/components/util/CourseCaptureBanner'
import Footer from '@/components/util/Footer'
import Snackbar from '@/components/util/Snackbar'
import Spinner from '@/components/util/Spinner'
import {getCasLogoutUrl} from '@/api/auth'
import {stripAnchorRef} from '@/lib/utils'
import {useContextStore} from '@/stores/context'

const contextStore = useContextStore()
const {config, currentUser, loading} = storeToRefs(contextStore)
const navItems = ref([])
const route = useRoute()
const router = useRouter()
const theme = useTheme()
const waveOptions = {
  cancellationPeriod: 75,
  color: ['#1abc9c', '#2980b9', '#2980b9', '#378dc5', '#378dc5', '#378dc5', '#d35400', '#f1c40f'][Math.floor(Math.random() * 8)],
  dissolveDuration: 0.4,
  duration: 1.8,
  easing: 'ease-out',
  finalOpacity: 0.1,
  initialOpacity: 0.2,
  tagName: 'div',
  trigger: 'auto'
}

onMounted(() => {
  prefersColorScheme()
  navItems.value = currentUser.value.courses.length ? [{title: 'Home', icon: mdiHome, path: '/home'}] : []
  if (currentUser.value.isAdmin) {
    navItems.value = navItems.value.concat([
      {title: 'Ouija Board', icon: mdiAutoFix, path: '/ouija'},
      {title: 'Rooms', icon: mdiDomain, path: '/rooms'},
      {title: 'Blackouts', icon: mdiVideoOffOutline, path: '/blackouts'},
      {title: 'Email Templates', icon: mdiEmailOpenMultipleOutline, path: '/email/templates'},
      {title: 'The Chancel', icon: mdiHandsPray, path: '/jobs'}
    ])
  } else {
    each(currentUser.value.courses, course => {
      if (course.meetings.eligible.length) {
        navItems.value.push({
          title: this.getCourseCodes(course)[0],
          icon: mdiVideoPlus,
          path: `/course/${config.value.currentTermId}/${course.sectionId}`
        })
      }
    })
  }
})

const logOut = () => {
  contextStore.alertScreenReader('Logging out')
  getCasLogoutUrl().then(data => window.location.href = data.casLogoutUrl)
}

const prefersColorScheme = () => {
  const mq = window.matchMedia('(prefers-color-scheme: dark)')
  const setColorScheme = prefersDark => {
    theme.global.name.value = prefersDark ? 'dark' : 'light'
  }
  setColorScheme(mq.matches)
  if (typeof mq.addEventListener === 'function') {
    mq.addEventListener('change', e => setColorScheme(e.matches))
  }
}

const toggleTheme = () => {
  theme.global.name.value = theme.global.current.value.dark ? 'light' : 'dark'
}
</script>

<style>
.sidebar-nav .v-list-item[aria-current="true"]:not(:focus)::before {
  opacity: 0.1;
}
</style>

<style scoped>
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
