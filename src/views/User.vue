<template>
  <div v-if="!loading">
    <v-card outlined class="elevation-1">
      <v-card-title>
        <PageTitle icon="mdi-school-outline" :text="`${user.name} (${user.uid})`" />
      </v-card-title>
      <v-card-subtitle class="body-1 ml-8 pl-12">
        <a :href="`mailto:${user.email}`" target="_blank">{{ user.email }}<span class="sr-only"> (new browser tab will open)</span></a>
      </v-card-subtitle>
      <CoursesDataTable
        class="pt-5"
        :courses="user.courses"
        :include-room-column="true"
        :message-for-courses="summarize(user.courses)"
        :on-toggle-opt-out="() => {}"
        :refreshing="false"
      />
    </v-card>
  </div>
</template>

<script>
  import Context from '@/mixins/Context'
  import CoursesDataTable from '@/components/course/CoursesDataTable'
  import PageTitle from '@/components/util/PageTitle'
  import Utils from '@/mixins/Utils'
  import {getUser} from '@/api/user'

  export default {
    name: 'Room',
    mixins: [Context, Utils],
    components: {CoursesDataTable, PageTitle},
    data: () => ({
      user: undefined
    }),
    created() {
      this.$loading()
      let uid = this.$_.get(this.$route, 'params.uid')
      getUser(uid).then(user => {
        this.user = user
        this.$_.each(this.user.courses, course => {
          course.courseCodes = this.getCourseCodes(course)
        })
        this.$ready(this.user.name)
      })
    }
  }
</script>
