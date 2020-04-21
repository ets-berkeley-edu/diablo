<template>
  <div v-if="!loading">
    <h2>{{ user.name }} ({{ user.uid }})</h2>
    <div class="pb-3">
      <a :href="`mailto:${user.campusEmail}`" target="_blank">{{ user.campusEmail }}<span class="sr-only"> (new browser tab will open)</span></a>
    </div>
    <v-card outlined class="elevation-1">
      <CoursesDataTable
        :courses="user.courses"
        message-when-zero-courses="No courses"
        :on-toggle-opt-out="() => {}"
        :refreshing="false"
      />
    </v-card>
  </div>
</template>

<script>
  import Context from '@/mixins/Context'
  import CoursesDataTable from '@/components/course/CoursesDataTable'
  import Utils from '@/mixins/Utils'
  import {getUser} from '@/api/user'

  export default {
    name: 'Room',
    components: {CoursesDataTable},
    mixins: [Context, Utils],
    data: () => ({
      user: undefined
    }),
    created() {
      this.$loading()
      let uid = this.$_.get(this.$route, 'params.uid')
      getUser(uid).then(user => {
        this.user = user
        this.setPageTitle(this.user.name)
        this.$ready()
      }).catch(this.$ready)
    }
  }
</script>
