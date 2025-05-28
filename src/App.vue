<template>
  <div>
    <span
      v-if="screenReaderAlert"
      id="screen-reader-alert"
      class="sr-only"
      aria-live="polite"
      role="alert"
    >
      {{ screenReaderAlert }}
    </span>
    <router-view />
  </div>
</template>

<script setup>
import {storeToRefs} from 'pinia'
import {useContextStore} from '@/stores/context'

const {screenReaderAlert} = storeToRefs(useContextStore())
</script>

<style>
@import 'v-calendar/style.css';
@import './assets/styles/vcalendar-custom.scss';
@import './assets/styles/tiptap/_variables.scss';
@import './assets/styles/tiptap/_keyframe-animations.scss';
@import './assets/styles/diablo-global.css';
</style>
