<template>
  <v-card v-if="!loading" outlined class="elevation-1">
    <v-card-title>
      <PageTitle icon="mdi-directions-fork" text="Course Changes" />
    </v-card-title>
    <v-card-text v-if="courses.length">
      <ObsoleteSchedule v-for="course in courses" :key="course.sectionId" :course="course" />
    </v-card-text>
    <v-card-text v-if="!courses.length" class="ma-4 text-no-wrap title">
      No changes within scheduled courses.
    </v-card-text>
  </v-card>
</template>

<script>
import Context from '@/mixins/Context'
import ObsoleteSchedule from '@/components/course/ObsoleteSchedule'
import PageTitle from '@/components/util/PageTitle'
import {getCourseChanges} from '@/api/course'

export default {
  name: 'CourseChanges',
  mixins: [Context],
  components: {ObsoleteSchedule, PageTitle},
  data: () => ({
    courses: undefined
  }),
  created() {
    this.$loading()
    getCourseChanges(this.$config.currentTermId).then(data => {
      this.courses = data
      this.$ready('Course Changes')
    })
  }
}
</script>
