<template>
  <div v-if="!loading">
    {{ room }}
  </div>
</template>

<script>
  import {getRoom} from '@/api/berkeley'

  export default {
    name: 'Room',
    data: () => ({
      room: undefined
    }),
    created() {
      let id = this.$_.get(this.$route, 'params.id')
      getRoom(id).then(room => {
        this.room = room
        this.$ready()
      })
    }
  }
</script>
