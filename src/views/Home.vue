<template>
  <div>
    Current user: {{ $currentUser }}
  </div>
</template>

<script>
  import axios from 'axios'

  export default {
    name: 'Home',
    data: () => ({
      foo: undefined
    }),
    created() {
      axios.get(`${process.env.VUE_APP_API_BASE_URL}/api/user/foo`).then(response => {
        this.foo = response.data
      })
    }
  }
</script>
