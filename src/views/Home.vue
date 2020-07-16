<template>
  <div v-if="!loading">
    <PageTitle icon="mdi-video-plus" :text="pageTitle" />
    <v-data-table
      disable-pagination
      disable-sort
      :headers="headers"
      :hide-default-footer="true"
      :items="courses"
      :items-per-page="100"
      class="elevation-1"
    >
      <template v-slot:body="{ items }">
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
                {{ course.meetings.eligible[0].room.location }}
              </td>
              <td :class="{'border-bottom-zero': course.meetings.eligible.length > 1}" class="text-no-wrap">
                {{ $_.join(course.meetings.eligible[0].daysFormatted, ', ') }}
              </td>
              <td :class="{'border-bottom-zero': course.meetings.eligible.length > 1}" class="text-no-wrap">
                <div v-if="course.nonstandardMeetingDates" class="pt-2">
                  <span class="text-no-wrap">{{ course.meetings.eligible[0].startDate | moment('MMM D, YYYY') }} - </span>
                  <span class="text-no-wrap">{{ course.meetings.eligible[0].endDate | moment('MMM D, YYYY') }}</span>
                </div>
                {{ course.meetings.eligible[0].startTimeFormatted }} - {{ course.meetings.eligible[0].endTimeFormatted }}
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
                {{ $_.join(course.meetings.eligible[index].daysFormatted, ', ') }}
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
        <tbody v-if="!items.length">
          <tr>
            <td id="message-when-zero-courses" class="ma-4 text-no-wrap title" :colspan="headers.length">
              <span>No courses.</span>
            </td>
          </tr>
        </tbody>
      </template>
    </v-data-table>
  </div>
</template>

<script>
  import Context from '@/mixins/Context'
  import PageTitle from '@/components/util/PageTitle'
  import Utils from '@/mixins/Utils'

  export default {
    name: 'Home',
    mixins: [Context, Utils],
    components: {PageTitle},
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
      this.pageTitle = `Your ${this.$config.currentTermName} Courses Eligible for Capture`
      this.courses = this.$_.filter(this.$currentUser.courses, course => {
        course.courseCodes = this.getCourseCodes(course)
        return course.meetings.eligible.length
      })
      this.$ready(this.pageTitle)
    }
  }
</script>
