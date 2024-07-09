<template>
  <v-card v-if="!loading" outlined class="elevation-1">
    <v-card-title>
      <PageTitle icon="mdi-video-plus" :text="pageTitle" />
    </v-card-title>
    <v-card-text>
      <v-row class="mx-4">
        <ToggleOptOut
          :term-id="`${$config.currentTermId}`"
          section-id="all"
          :instructor-uid="$currentUser.uid"
          :initial-value="$currentUser.hasOptedOutForTerm"
          :disabled="$currentUser.hasOptedOutForAllTerms"
          label="Opt out for current semester"
          :before-toggle="() => refreshingCourses = true"
          :on-toggle="reloadCoursesTable"
        />
      </v-row>
      <v-row class="mx-4 mt-0 mb-2">
        <ToggleOptOut
          term-id="all"
          section-id="all"
          :instructor-uid="$currentUser.uid"
          :initial-value="$currentUser.hasOptedOutForAllTerms"
          label="Opt out for all semesters"
          :before-toggle="() => refreshingCourses = true"
          :on-toggle="reloadCoursesTable"
        />
      </v-row>
      <Spinner v-if="refreshingCourses" />
      <v-data-table
        v-if="!refreshingCourses && courses.length"
        disable-pagination
        disable-sort
        :headers="headers"
        :hide-default-footer="true"
        :items="courses"
        :items-per-page="100"
        class="elevation-1"
      >
        <template #body="{items}">
          <tbody>
            <template v-for="course in items" :id="`course-${course.sectionId}`">
              <tr :key="course.sectionId">
                <td class="text-no-wrap" :class="{'pt-3 pb-3': course.courseCodes.length > 1, 'border-bottom-zero': course.meetings.eligible.length > 1}">
                  <div v-for="(courseCode, index) in course.courseCodes" :key="courseCode">
                    <router-link
                      v-if="index === 0"
                      :id="`link-course-${course.sectionId}`"
                      :to="`/course/${$config.currentTermId}/${course.sectionId}`"
                    >
                      {{ courseCode }}
                    </router-link>
                    <span v-if="index > 0">{{ courseCode }}</span>
                  </div>
                </td>
                <td :class="{'border-bottom-zero': course.meetings.eligible.length > 1}">
                  {{ course.courseTitle || '&mdash;' }}
                </td>
                <td :class="{'border-bottom-zero': course.meetings.eligible.length > 1}">
                  {{ oxfordJoin($_.map(course.instructors, 'name')) }}
                </td>
                <td :class="{'border-bottom-zero': course.meetings.eligible.length > 1}" class="text-no-wrap">
                  {{ course.meeting.room.location }}
                </td>
                <td :class="{'border-bottom-zero': course.meetings.eligible.length > 1}" class="text-no-wrap">
                  <Days v-if="course.meeting.daysNames.length" :names-of-days="course.meeting.daysNames" />
                  <span v-if="!course.meeting.daysNames.length">&mdash;</span>
                </td>
                <td :class="{'border-bottom-zero': course.meetings.eligible.length > 1}" class="text-no-wrap">
                  <div v-if="course.nonstandardMeetingDates" class="pt-2">
                    <span class="text-no-wrap">{{ course.meeting.startDate | moment('MMM D, YYYY') }} - </span>
                    <span class="text-no-wrap">{{ course.meeting.endDate | moment('MMM D, YYYY') }}</span>
                  </div>
                  {{ course.meeting.startTimeFormatted }} - {{ course.meeting.endTimeFormatted }}
                </td>
                <td :class="{'border-bottom-zero': course.meetings.eligible.length > 1}" class="text-no-wrap">
                  <ToggleOptOut
                    :term-id="`${course.termId}`"
                    :section-id="`${course.sectionId}`"
                    :instructor-uid="$currentUser.uid"
                    :initial-value="course.hasOptedOut"
                    :disabled="course.hasBlanketOptedOut"
                  />
                </td>
              </tr>
              <tr v-for="index in course.meetings.eligible.length - 1" :key="index">
                <td></td>
                <td></td>
                <td></td>
                <td class="pt-0 text-no-wrap">
                  {{ course.meetings.eligible[index].room.location }}
                </td>
                <td class="text-no-wrap">
                  <Days :names-of-days="course.meetings.eligible[index].daysNames" />
                </td>
                <td class="text-no-wrap">
                  <div v-if="course.nonstandardMeetingDates" class="pt-2">
                    <span class="text-no-wrap">{{ course.meetings.eligible[index].startDate | moment('MMM D, YYYY') }} - </span>
                    <span class="text-no-wrap">{{ course.meetings.eligible[index].endDate | moment('MMM D, YYYY') }}</span>
                  </div>
                  <div :class="{'pb-2': course.nonstandardMeetingDates && index === course.meetings.eligible.length - 1}">
                    {{ course.meetings.eligible[index].startTimeFormatted }} - {{ course.meetings.eligible[index].endTimeFormatted }}
                  </div>
                </td>
                <td></td>
              </tr>
            </template>
          </tbody>
        </template>
      </v-data-table>
      <v-row v-if="!courses.length" class="ma-4 text-no-wrap title">
        No courses.
      </v-row>
    </v-card-text>
  </v-card>
</template>

<script>
import Context from '@/mixins/Context'
import Days from '@/components/util/Days'
import PageTitle from '@/components/util/PageTitle'
import Spinner from '@/components/util/Spinner'
import ToggleOptOut from '@/components/course/ToggleOptOut'
import Utils from '@/mixins/Utils'

export default {
  name: 'Home',
  mixins: [Context, Utils],
  components: {Days, PageTitle, Spinner, ToggleOptOut},
  data: () => ({
    courses: undefined,
    headers: [
      {text: 'Course', value: 'label'},
      {text: 'Title', value: 'title'},
      {text: 'Instructors', value: 'instructors'},
      {text: 'Room', value: 'room'},
      {text: 'Days', value: 'days'},
      {text: 'Time', value: 'time'},
      {text: 'Opt out', value: 'hasOptedOut'}
    ],
    pageTitle: undefined,
    refreshingCourses: false,
  }),
  created() {
    this.$loading()
    this.refreshCourses()
    console.log(this.$currentUser)
    this.pageTitle = `Your ${this.$config.currentTermName} Course${this.courses.length === 1 ? '' : 's'} Eligible for Capture`
    this.$ready(this.pageTitle)
  },
  methods: {
    refreshCourses() {
      this.courses = this.$_.filter(this.$currentUser.courses, course => {
        course.courseCodes = this.getCourseCodes(course)
        const isEligible = course.meetings.eligible.length
        if (isEligible) {
          course.meeting = this.getDisplayMeetings(course)[0]
        }
        return isEligible
      })
    },
    reloadCoursesTable() {
      this.$refreshCurrentUser().then(() => {
        this.refreshCourses()
        this.refreshingCourses = false
      })
    }
  }
}
</script>
