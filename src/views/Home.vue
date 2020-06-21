<template>
  <div v-if="!loading">
    <div class="pb-3">
      <h1>{{ pageTitle }}</h1>
    </div>
    <v-data-table
      disable-pagination
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
              <td class="text-no-wrap" :class="{'pt-3 pb-3': course.courseCodes.length > 1, 'border-bottom-zero': course.meetings.length > 1}">
                <div v-for="(courseCode, index) in course.courseCodes" :key="courseCode">
                  <router-link
                    v-if="course.room && course.room.capability && index === 0"
                    :id="`link-course-${course.sectionId}`"
                    :to="`/course/${$config.currentTermId}/${course.sectionId}`"
                  >
                    {{ courseCode }}
                  </router-link>
                  <span v-if="index > 0 || !course.room || !course.room.capability">{{ courseCode }}</span>
                </div>
              </td>
              <td :class="{'border-bottom-zero': course.meetings.length > 1}">
                {{ course.title || '&mdash;' }}
              </td>
              <td :class="{'border-bottom-zero': course.meetings.length > 1}">
                {{ oxfordJoin($_.map(course.instructors, 'name')) }}
              </td>
              <td :class="{'border-bottom-zero': course.meetings.length > 1}" class="text-no-wrap">
                {{ course.meetings[0].room.location }}
              </td>
              <td :class="{'border-bottom-zero': course.meetings.length > 1}" class="text-no-wrap">
                {{ $_.join(course.meetings[0].daysFormatted, ', ') }}
              </td>
              <td :class="{'border-bottom-zero': course.meetings.length > 1}" class="text-no-wrap">
                {{ course.meetings[0].startTimeFormatted }} - {{ course.meetings[0].endTimeFormatted }}
              </td>
            </tr>
            <tr v-for="index in course.meetings.length - 1" :key="index">
              <td></td>
              <td></td>
              <td></td>
              <td class="pt-0 text-no-wrap">
                {{ course.meetings[index].room.location }}
              </td>
              <td class="text-no-wrap">
                {{ $_.join(course.meetings[index].daysFormatted, ', ') }}
              </td>
              <td class="text-no-wrap">
                {{ course.meetings[index].startTimeFormatted }} - {{ course.meetings[index].endTimeFormatted }}
              </td>
            </tr>
          </template>
        </tbody>
      </template>
    </v-data-table>
  </div>
</template>

<script>
  import Context from '@/mixins/Context'
  import Utils from '@/mixins/Utils'

  export default {
    name: 'Home',
    mixins: [Context, Utils],
    data: () => ({
      courses: undefined,
      headers: [
        {text: 'Course', value: 'label'},
        {text: 'Title', value: 'title'},
        {text: 'Instructors', value: 'instructors', sortable: false},
        {text: 'Room', value: 'room', sortable: false},
        {text: 'Days', value: 'days', sortable: false},
        {text: 'Time', value: 'time', sortable: false}
      ],
      pageTitle: undefined
    }),
    created() {
      this.$loading()
      this.pageTitle = `Your ${this.$config.currentTermName} Courses Eligible for Capture`
      this.courses = this.$_.filter(this.$currentUser.courses, course => {
        course.courseCodes = this.getCourseCodes(course)
        course.meetings = this.$_.filter(course.meetings, m => m.room && m.room.capability)
        return course.meetings.length
      })
      this.$ready(this.pageTitle)
    }
  }
</script>
