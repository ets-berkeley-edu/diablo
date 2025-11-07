<template>
  <div class="banner not-selectable ml-4" :class="{'mood-ring': theme.global.current.value.dark}">
    <v-expand-x-transition><div v-if="showPrefix" class="text-white">This is</div></v-expand-x-transition>
    <b>
      <div class="banner-inner">
        <div class="w-100">Course Capture</div>
        <div class="w-100">{{ contextStore.config.currentTermName }}</div>
      </div>
    </b>
  </div>
</template>

<script setup>
import {onMounted, ref} from 'vue'
import {useTheme} from 'vuetify'
import {useContextStore} from '@/stores/context'

const contextStore = useContextStore()
const showPrefix = ref(true)
const theme = useTheme()

onMounted(() => {
  setTimeout(() => {
    showPrefix.value = false
  }, 5000)
})
</script>

<style scoped>
.banner {
  font: normal 40px/50px Montserrat, sans-serif;
}
.banner div {
  height: 50px;
  float: left;
  margin-right: 0.3em;
}
.banner b {
  float: left;
  overflow: hidden;
  position: relative;
  height: 50px;
  top: 0;
}
.banner .banner-inner {
  display: inline-block;
  position: relative;
  white-space: nowrap;
  top: 0;
  left: 0;
  /*animation*/
  -webkit-animation:move 2s;
     -moz-animation:move 2s;
      -ms-animation:move 2s;
       -o-animation:move 2s;
          animation:move 2s;
  /*animation-iteration-count*/
  -webkit-animation-iteration-count: 1;
     -moz-animation-iteration-count: 1;
      -ms-animation-iteration-count: 1;
       -o-animation-iteration-count: 1;
          animation-iteration-count: 1;
  /*animation-delay*/
  -webkit-animation-delay: 1s;
     -moz-animation-delay: 1s;
      -ms-animation-delay: 1s;
       -o-animation-delay: 1s;
          animation-delay: 1s;
}
.mood-ring {
  -webkit-animation: moods 300s infinite alternate;
  animation: moods 300s infinite alternate;
}
.v-enter-active,
.v-leave-active {
  transition: opacity 1.0s ease;
}
.v-enter-from,
.v-leave-to {
  opacity: 0;
}
@keyframes moods {
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
@keyframes move {
  0%  { top: 0px; }
  50% { top: -50px; }
}
@-webkit-keyframes move {
  0%  { top: 0px; }
  50% { top: -50px; }
}
@-moz-keyframes move {
  0%  { top: 0px; }
  50% { top: -50px; }
}
@-o-keyframes move {
  0%  { top: 0px; }
  50% { top: -50px; }
}
@keyframes move {
  0%  { top: 0px; }
  50% { top: -50px; }
}
</style>
