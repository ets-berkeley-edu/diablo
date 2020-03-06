<template>
  <div>
    <h1>Your {{ $config.currentTermName }} courses</h1>
    <v-data-table
      :headers="headers"
      :hide-default-footer="true"
      :items="showEligibleCoursesOnly ? coursesEligibleOnly : courses"
      :items-per-page="100"
      :loading="loading"
      class="elevation-1 text-no-wrap"
    >
      <template v-slot:top>
        <div class="d-flex">
          <div class="pa-5">
            <label for="show-only-eligible-courses" class="text--darken-2">Show only courses eligible for Course Capture?</label>
          </div>
          <div>
            <v-switch
              id="show-only-eligible-courses"
              v-model="showEligibleCoursesOnly"
            ></v-switch>
          </div>
          <div class="pt-5">
            {{ showEligibleCoursesOnly ? 'Yes' : 'No' }}
          </div>
        </div>
      </template>
    </v-data-table>
  </div>
</template>

<script>
  import Utils from '@/mixins/Utils'

  export default {
    name: 'Home',
    mixins: [Utils],
    data: () => ({
      courses: undefined,
      coursesEligibleOnly: undefined,
      headers: [
        {text: 'Course', value: 'course', class: 'text-no-wrap'},
        {text: 'Title', value: 'title'},
        {text: 'Instructors', value: 'instructors', sortable: false},
        {text: 'Location', value: 'location'},
        {text: 'Schedule', value: 'schedule', sortable: false}
      ],
      loading: true,
      showEligibleCoursesOnly: false
    }),
    created() {
      this.courses = []
      this.coursesEligibleOnly = []
      this.$_.each(this.$currentUser.teachingSections, s => {
        let course = {
          course: `${s.courseName}, ${s.instructionFormat} ${s.sectionNum}`,
          title: s.courseTitle,
          schedule: this.describeSchedule(s),
          instructors: this.oxfordJoin(this.$_.map(s.instructors, 'name')),
          location: s.meetingLocation
        }
        this.courses.push(course)
        if (s.isEligibleForCourseCapture) {
          this.coursesEligibleOnly.push(course)
        }
      })
      this.loading = false
    },
    methods: {
      describeSchedule(section) {
        return section.meetingDays ? `${section.meetingStartTime} - ${section.meetingEndTime}, ${section.meetingDays}` : undefined
      }
    }
  }
</script>
