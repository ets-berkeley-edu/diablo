<template>
  <span>{{ profile ? formatter(profile) : `UID ${uid}` }}</span>
</template>

<script>
import {getCalnetUser} from '@/api/user'

export default {
  name: 'CalNetProfile',
  props: {
    formatter: {
      default: profile => profile.name,
      required: false,
      type: Function
    },
    uid: {
      required: true,
      type: String
    }
  },
  data: () => ({
    profile: undefined
  }),
  created() {
    getCalnetUser(this.uid).then(data => {
      this.profile = data
    })
  }
}
</script>
