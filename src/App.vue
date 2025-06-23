<template>
  <div>
    <div
      id="screen-reader-alert"
      class="sr-only"
      :aria-live="ariaLive"
      :role="ariaLive === 'assertive' ? 'alert' : undefined"
    >
      <span v-if="get(screenReaderAlert, 'message', '').length">
        {{ screenReaderAlert.message }}
      </span>
    </div>
    <router-view />
  </div>
</template>

<script setup>
import {computed} from 'vue'
import {get} from 'lodash'
import {storeToRefs} from 'pinia'
import {useContextStore} from '@/stores/context'

const {screenReaderAlert} = storeToRefs(useContextStore())
const ariaLive = computed(() => get(screenReaderAlert, 'politeness', 'polite'))
</script>

<style>
@import 'v-calendar/style.css';
@import './assets/styles/vcalendar-custom.scss';
@import './assets/styles/tiptap/_variables.scss';
@import './assets/styles/tiptap/_keyframe-animations.scss';
@import './assets/styles/diablo-global.css';
</style>
