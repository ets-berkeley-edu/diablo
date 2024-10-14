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
          label="for current semester"
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
          label="for all semesters"
          :before-toggle="() => refreshingCourses = true"
          :on-toggle="reloadCoursesTable"
        />
      </v-row>
      <Spinner v-if="refreshingCourses" />
      <template v-for="(courses, index) in [eligibleCourses, ineligibleCourses]">
        <v-row v-if="!refreshingCourses && courses.length" :key="index">
          <h2 class="px-4">
            {{ index === 0 ? 'Courses eligible for capture' : 'Courses not in a course capture classroom' }}
          </h2>
          <v-data-table
            :id="index === 0 ? 'courses-table-eligible' : 'courses-table-ineligible'"
            disable-pagination
            disable-sort
            :headers="index === 0 ? eligibleHeaders : ineligibleHeaders"
            :hide-default-footer="true"
            :items="courses"
            :items-per-page="100"
            class="elevation-1 w-100 ma-4"
          >
            <template #body="{items}">
              <tbody>
                <template v-for="course in items" :id="`course-${course.sectionId}`">
                  <tr :key="course.sectionId">
                    <td class="text-no-wrap" :class="{'pt-3 pb-3': course.courseCodes.length > 1, 'border-bottom-zero': course.displayMeetings.length > 1}">
                      <div v-for="(courseCode, courseCodeIndex) in course.courseCodes" :key="courseCode">
                        <router-link
                          v-if="courseCodeIndex === 0"
                          :id="`link-course-${course.sectionId}`"
                          :to="`/course/${$config.currentTermId}/${course.sectionId}`"
                        >
                          {{ courseCode }}
                        </router-link>
                        <span v-if="courseCodeIndex > 0">{{ courseCode }}</span>
                      </div>
                    </td>
                    <td :class="{'border-bottom-zero': course.displayMeetings.length > 1}">
                      {{ course.courseTitle || '&mdash;' }}
                    </td>
                    <td :class="{'border-bottom-zero': course.displayMeetings.length > 1}">
                      {{ oxfordJoin($_.map(course.instructors, 'name')) }}
                    </td>
                    <td :class="{'border-bottom-zero': course.displayMeetings.length > 1}" class="text-no-wrap">
                      {{ course.displayMeetings[0].room.location }}
                    </td>
                    <td :class="{'border-bottom-zero': course.displayMeetings.length > 1}" class="text-no-wrap">
                      <Days v-if="course.displayMeetings[0].daysNames.length" :names-of-days="course.displayMeetings[0].daysNames" />
                      <span v-if="!course.displayMeetings[0].daysNames.length">&mdash;</span>
                    </td>
                    <td :class="{'border-bottom-zero': course.displayMeetings.length > 1}" class="text-no-wrap">
                      <div v-if="course.nonstandardMeetingDates" class="pt-2">
                        <span class="text-no-wrap">{{ course.displayMeetings[0].startDate | moment('MMM D, YYYY') }} - </span>
                        <span class="text-no-wrap">{{ course.displayMeetings[0].endDate | moment('MMM D, YYYY') }}</span>
                      </div>
                      {{ course.displayMeetings[0].startTimeFormatted }} - {{ course.displayMeetings[0].endTimeFormatted }}
                    </td>
                    <td v-if="index === 0" :class="{'border-bottom-zero': course.displayMeetings[0].eligible.length > 1}" class="text-no-wrap">
                      <ToggleOptOut
                        :aria-label="`Opt out course ${course.courseTitle || $_.get(course.courseCodes, '0', '')}.`"
                        :disabled="course.hasBlanketOptedOut"
                        :initial-value="course.hasOptedOut"
                        :instructor-uid="$currentUser.uid"
                        :section-id="`${course.sectionId}`"
                        :term-id="`${course.termId}`"
                      />
                    </td>
                  </tr>
                  <tr v-for="meetingIndex in course.displayMeetings.length - 1" :key="meetingIndex">
                    <td></td>
                    <td></td>
                    <td></td>
                    <td class="pt-0 text-no-wrap">
                      {{ course.displayMeetings[meetingIndex].room.location }}
                    </td>
                    <td class="text-no-wrap">
                      <Days :names-of-days="course.displayMeetings[meetingIndex].daysNames" />
                    </td>
                    <td class="text-no-wrap">
                      <div v-if="course.nonstandardMeetingDates" class="pt-2">
                        <span class="text-no-wrap">{{ course.displayMeetings[meetingIndex].startDate | moment('MMM D, YYYY') }} - </span>
                        <span class="text-no-wrap">{{ course.displayMeetings[meetingIndex].endDate | moment('MMM D, YYYY') }}</span>
                      </div>
                      <div :class="{'pb-2': course.nonstandardMeetingDates && meetingIndex === course.displayMeetings.length - 1}">
                        {{ course.displayMeetings[meetingIndex].startTimeFormatted }} - {{ course.displayMeetings[meetingIndex].endTimeFormatted }}
                      </div>
                    </td>
                    <td></td>
                  </tr>
                </template>
              </tbody>
            </template>
          </v-data-table>
        </v-row>
      </template>
      <v-row v-if="!eligibleCourses.length && !ineligibleCourses.length" class="ma-4 text-no-wrap title">
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
    eligibleCourses: [],
    ineligibleCourses: [],
    headers: [
      {text: 'Course', value: 'label'},
      {text: 'Title', value: 'title'},
      {text: 'Instructors', value: 'instructors'},
      {text: 'Room', value: 'room'},
      {text: 'Days', value: 'days'},
      {text: 'Time', value: 'time'},
    ],
    pageTitle: undefined,
    refreshingCourses: false,
  }),
  created() {
    this.$loading()
    this.eligibleHeaders = this.headers.concat({text: 'Opt out', value: 'hasOptedOut'})
    this.ineligibleHeaders = this.headers
    this.refreshCourses()
    this.pageTitle = `Your ${this.$config.currentTermName} Course${this.$currentUser.courses.length === 1 ? '' : 's'}`
    this.$ready(this.pageTitle)
  },
  methods: {
    refreshCourses() {
      this.$_.each(this.$currentUser.courses, course => {
        course.courseCodes = this.getCourseCodes(course)
      })
      this.eligibleCourses = []
      this.ineligibleCourses = []
      this.partitionCoursesByEligibility(this.$currentUser.courses, this.eligibleCourses, this.ineligibleCourses)
      this.$_.each([...this.eligibleCourses, ...this.ineligibleCourses], course => {
        course.displayMeetings = this.getDisplayMeetings(course)
      })
    },
    reloadCoursesTable(srAlert = '') {
      this.$refreshCurrentUser().then(() => {
        this.refreshCourses()
        this.refreshingCourses = false
        this.alertScreenReader(`Courses table refreshed. ${srAlert}`)
      })
    }
  }
}
</script>
