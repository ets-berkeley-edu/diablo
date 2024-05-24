<template>
  <div v-if="!loading">
    <v-card outlined class="elevation-1">
      <v-card-title>
        <PageTitle icon="mdi-school-outline" :text="`${user.name} (${user.uid})`" />
      </v-card-title>
      <v-card-subtitle class="body-1 ml-8 pl-12">
        <a :href="`mailto:${user.email}`" target="_blank">{{ user.email }}<span class="sr-only"> (new browser tab will open)</span></a>
      </v-card-subtitle>
      <v-row class="mx-4">
        <ToggleOptOut
          :term-id="`${$config.currentTermId}`"
          section-id="all"
          :instructor-uid="user.uid"
          :initial-value="user.hasOptedOutForTerm"
          :disabled="user.hasOptedOutForAllTerms"
          label="Opt out for current semester"
          :before-toggle="() => refreshingCourses = true"
          :on-toggle="refreshUser"
        />
      </v-row>
      <v-row class="mx-4 mt-0 mb-2">
        <ToggleOptOut
          term-id="all"
          section-id="all"
          :instructor-uid="user.uid"
          :initial-value="user.hasOptedOutForAllTerms"
          label="Opt out for all semesters"
          :before-toggle="() => refreshingCourses = true"
          :on-toggle="refreshUser"
        />
      </v-row>
      <Spinner v-if="refreshingCourses" />
      <CoursesDataTable
        v-if="!refreshingCourses"
        class="pt-5"
        :courses="user.courses"
        :include-room-column="true"
        :include-opt-out-column-for-uid="user.uid"
        :message-for-courses="summarize(user.courses)"
        :refreshing="false"
      />
    </v-card>
  </div>
</template>

<script>
import Context from '@/mixins/Context'
import CoursesDataTable from '@/components/course/CoursesDataTable'
import PageTitle from '@/components/util/PageTitle'
import Spinner from '@/components/util/Spinner'
import ToggleOptOut from '@/components/course/ToggleOptOut'
import Utils from '@/mixins/Utils'
import {getUser} from '@/api/user'

export default {
  name: 'Room',
  mixins: [Context, Utils],
  components: {CoursesDataTable, PageTitle, Spinner, ToggleOptOut},
  data: () => ({
    refreshingCourses: false,
    uid: undefined,
    user: undefined
  }),
  created() {
    this.$loading()
    this.uid = this.$_.get(this.$route, 'params.uid')
    this.refreshUser()
  },
  methods: {
    refreshUser() {
      getUser(this.uid).then(user => {
        this.user = user
        this.$_.each(this.user.courses, course => {
          course.courseCodes = this.getCourseCodes(course)
        })
        this.$ready(this.user.name)
        this.refreshingCourses = false
      })
    }
  }
}
</script>
