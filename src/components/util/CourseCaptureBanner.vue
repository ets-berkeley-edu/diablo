<template>
  <div class="banner">
    <transition><div v-if="showPrefix">This is</div></transition>
    <b>
      <div class="banner-inner">
        Course Capture<br />
        {{ $config.currentTermName }}<br />
        Bear Territory
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
    }, 8000)
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
  top: 0px;
}
.banner .banner-inner {
  display: inline-block;
  color: #e74c3c;
  position: relative;
  white-space: nowrap;
  top: 0;
  left: 0;

  /*animation*/
  -webkit-animation:move 5s;
     -moz-animation:move 5s;
      -ms-animation:move 5s;
       -o-animation:move 5s;
          animation:move 5s;
  /*animation-iteration-count*/
  -webkit-animation-iteration-count: 1;
     -moz-animation-iteration-count: 1;
      -ms-animation-iteration-count: 1;
       -o-animation-iteration-count: 1;
          animation-iteration-count: 1;
  /*animation-delay*/
  -webkit-animation-delay: 2s;
     -moz-animation-delay: 2s;
      -ms-animation-delay: 2s;
       -o-animation-delay: 2s;
          animation-delay: 2s;
}
.v-enter-active,
.v-leave-active {
  transition: opacity 1.0s ease-out;
}
.v-enter-from,
.v-leave-to {
  opacity: 0;
}
@keyframes move {
  0%  { top: 0px; }
  20% { top: -50px; }
  40% { top: -100px; }
}
@-webkit-keyframes move {
  0%  { top: 0px; }
  20% { top: -50px; }
  40% { top: -100px; }
}
@-moz-keyframes move {
  0%  { top: 0px; }
  20% { top: -50px; }
  40% { top: -100px; }
}
@-o-keyframes move {
  0%  { top: 0px; }
  20% { top: -50px; }
  40% { top: -100px; }
}
@keyframes move {
  0%  { top: 0px; }
  20% { top: -50px; }
  40% { top: -100px; }
}
</style>
