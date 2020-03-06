<template>
  <div class="ma-4">
    <router-view :key="$route.fullPath"></router-view>
  </div>
</template>

<script>
  export default {
    name: 'BaseView'
  }
</script>
