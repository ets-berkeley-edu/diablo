<template>
  <v-card v-if="!loading" outlined class="elevation-1">
    <v-card-title>
      <PageTitle icon="mdi-video-plus" :text="pageTitle" />
    </v-card-title>
    <v-card-text v-if="courses.length">
      <v-data-table
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
              </tr>
            </template>
          </tbody>
        </template>
      </v-data-table>
    </v-card-text>
    <v-card-text v-if="!courses.length" class="ma-4 text-no-wrap title">
      No courses.
    </v-card-text>
  </v-card>
</template>

<script>
import Context from '@/mixins/Context'
import Days from '@/components/util/Days'
import PageTitle from '@/components/util/PageTitle'
import Utils from '@/mixins/Utils'

export default {
  name: 'Home',
  mixins: [Context, Utils],
  components: {Days, PageTitle},
  data: () => ({
    courses: undefined,
    headers: [
      {text: 'Course', value: 'label'},
      {text: 'Title', value: 'title'},
      {text: 'Instructors', value: 'instructors'},
      {text: 'Room', value: 'room'},
      {text: 'Days', value: 'days'},
      {text: 'Time', value: 'time'}
    ],
    pageTitle: undefined
  }),
  created() {
    this.$loading()
    this.courses = this.$_.filter(this.$currentUser.courses, course => {
      course.courseCodes = this.getCourseCodes(course)
      const isEligible = course.meetings.eligible.length
      if (isEligible) {
        course.meeting = this.getDisplayMeetings(course)[0]
      }
      return isEligible
    })
    this.pageTitle = `Your ${this.$config.currentTermName} Course${this.courses.length === 1 ? '' : 's'} Eligible for Capture`
    this.$ready(this.pageTitle)
  }
}
</script>
