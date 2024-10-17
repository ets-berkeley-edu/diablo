<template>
  <v-card
    v-if="!loading"
    class="elevation-1"
    min-width="880"
    outlined
  >
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
        <v-row v-if="!refreshingCourses && courses.length" :key="index" class="py-2">
          <h2 class="px-4">
            {{ index === 0 ? 'Courses eligible for capture' : 'Courses not in a course capture classroom' }}
          </h2>
          <v-data-table
            :id="getTableId(index)"
            :caption="index === 0 ? 'Courses eligible for capture' : 'Courses not in a course capture classroom'"
            disable-pagination
            disable-sort
            :headers="index === 0 ? eligibleHeaders : ineligibleHeaders"
            :hide-default-footer="true"
            :hide-default-header="true"
            :items="courses"
            :items-per-page="100"
            class="elevation-1 w-100 ma-4"
          >
            <template #header="{props: {headers: columns}}">
              <thead>
                <tr>
                  <th
                    v-for="(column, colIndex) in columns"
                    :id="`${getTableId(index)}-${column.value}-th`"
                    :key="colIndex"
                    class="text-start text-no-wrap"
                    scope="col"
                  >
                    <span class="font-size-12 font-weight-bold">{{ column.text }}</span>
                  </th>
                </tr>
              </thead>
            </template>
            <template #body="{items}">
              <tbody>
                <template v-for="course in items" :id="`${getTableId(index)}-${course.sectionId}`">
                  <tr :key="course.sectionId">
                    <td
                      :id="`${getTableId(index)}-${course.sectionId}-label`"
                      class="text-no-wrap"
                      :class="{'pt-3 pb-3': course.courseCodes.length > 1, 'border-bottom-zero': course.displayMeetings.length > 1}"
                      :columnheader="`${getTableId(index)}-label-th`"
                    >
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
                    <td
                      :id="`${getTableId(index)}-${course.sectionId}-title`"
                      :class="{'border-bottom-zero': course.displayMeetings.length > 1}"
                      :columnheader="`${getTableId(index)}-title-th`"
                    >
                      <span aria-hidden="true">{{ course.courseTitle || '&mdash;' }}</span>
                      <span class="sr-only">{{ course.courseTitle || 'blank' }}</span>
                    </td>
                    <td
                      :id="`${getTableId(index)}-${course.sectionId}-instructors`"
                      :class="{'border-bottom-zero': course.displayMeetings.length > 1}"
                      :columnheader="`${getTableId(index)}-instructors-th`"
                    >
                      {{ oxfordJoin($_.map(course.instructors, 'name')) }}
                    </td>
                    <td
                      :id="`${getTableId(index)}-${course.sectionId}-room-0`"
                      :class="{'border-bottom-zero': course.displayMeetings.length > 1}"
                      class="text-no-wrap"
                      :columnheader="`${getTableId(index)}-room-th`"
                    >
                      {{ course.displayMeetings[0].room.location }}
                    </td>
                    <td
                      :id="`${getTableId(index)}-${course.sectionId}-days-0`"
                      :class="{'border-bottom-zero': course.displayMeetings.length > 1}"
                      class="text-no-wrap"
                      :columnheader="`${getTableId(index)}-days-th`"
                    >
                      <Days v-if="course.displayMeetings[0].daysNames.length" :names-of-days="course.displayMeetings[0].daysNames" />
                      <span v-if="!course.displayMeetings[0].daysNames.length">&mdash;</span>
                    </td>
                    <td
                      :id="`${getTableId(index)}-${course.sectionId}-time-0`"
                      :class="{'border-bottom-zero': course.displayMeetings.length > 1}"
                      class="text-no-wrap"
                      :columnheader="`${getTableId(index)}-time-th`"
                    >
                      <div v-if="course.nonstandardMeetingDates" class="pt-2">
                        <span class="text-no-wrap">{{ course.displayMeetings[0].startDate | moment('MMM D, YYYY') }} - </span>
                        <span class="text-no-wrap">{{ course.displayMeetings[0].endDate | moment('MMM D, YYYY') }}</span>
                      </div>
                      <span aria-hidden="true">{{ course.displayMeetings[0].startTimeFormatted }} - {{ course.displayMeetings[0].endTimeFormatted }}</span>
                      <span class="sr-only">{{ course.displayMeetings[0].startTimeFormatted }} to {{ course.displayMeetings[0].endTimeFormatted }}</span>
                    </td>
                    <td
                      v-if="index === 0"
                      :id="`${getTableId(index)}-${course.sectionId}-hasOptedOut`"
                      :class="{'border-bottom-zero': course.displayMeetings[0].eligible.length > 1}"
                      class="text-no-wrap"
                      :columnheader="`${getTableId(index)}-hasOptedOut-th`"
                    >
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
                    <td
                      :id="`${getTableId(index)}-${course.sectionId}-room-${index}`"
                      class="pt-0 text-no-wrap"
                      :columnheader="`${getTableId(index)}-room-th`"
                    >
                      {{ course.displayMeetings[meetingIndex].room.location }}
                    </td>
                    <td
                      :id="`${getTableId(index)}-${course.sectionId}-days-${index}`"
                      class="text-no-wrap"
                      :columnheader="`${getTableId(index)}-days-th`"
                    >
                      <Days :names-of-days="course.displayMeetings[meetingIndex].daysNames" />
                    </td>
                    <td
                      :id="`${getTableId(index)}-${course.sectionId}-time-${index}`"
                      class="text-no-wrap"
                      :columnheader="`${getTableId(index)}-time-th`"
                    >
                      <div v-if="course.nonstandardMeetingDates" class="pt-2">
                        <span class="text-no-wrap">{{ course.displayMeetings[meetingIndex].startDate | moment('MMM D, YYYY') }} - </span>
                        <span class="text-no-wrap">{{ course.displayMeetings[meetingIndex].endDate | moment('MMM D, YYYY') }}</span>
                      </div>
                      <div :class="{'pb-2': course.nonstandardMeetingDates && meetingIndex === course.displayMeetings.length - 1}">
                        {{ course.displayMeetings[meetingIndex].startTimeFormatted }} - {{ course.displayMeetings[meetingIndex].endTimeFormatted }}
                      </div>
                    </td>
                    <td v-if="index === 0"></td>
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
    getTableId(index) {
      return index === 0 ? 'courses-table-eligible' : 'courses-table-ineligible'
    },
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
