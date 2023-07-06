<template>
  <div class="banner">
    <transition><div v-if="showPrefix">This is</div></transition>
    <b>
      <div class="banner-inner" :style="`color: ${$config.uxBannerColor}`">
        Course Capture<br />
        {{ $config.currentTermName }}
      </div>
    </b>
  </div>
</template>

<script>
export default {
  name: 'CourseCaptureBanner',
  data: () => ({
    showPrefix: true
  }),
  created() {
    setTimeout(() => {
      this.showPrefix = false
    }, 5000)
  }
}
</script>

<style scoped>
.banner {
  font: normal 40px/50px Montserrat, sans-serif;
  color: #999;
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
.v-enter-active,
.v-leave-active {
  transition: opacity 1.0s ease;
}
.v-enter-from,
.v-leave-to {
  opacity: 0;
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
