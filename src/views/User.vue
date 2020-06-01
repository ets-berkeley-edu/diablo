<template>
  <div v-if="!loading">
    <h1>{{ user.name }} ({{ user.uid }})</h1>
    <div class="pb-3">
      <a :href="`mailto:${user.campusEmail}`" target="_blank">{{ user.campusEmail }}<span class="sr-only"> (new browser tab will open)</span></a>
    </div>
    <v-card outlined class="elevation-1">
      <CoursesDataTable
        class="pt-5"
        :courses="user.courses"
        :message-for-courses="getMessageForCourses()"
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
        this.$ready(this.user.name)
      }).catch(this.$ready)
    },
    methods: {
      getMessageForCourses() {
        return this.summarize(this.user.courses)
      }
    }
  }
</script>
