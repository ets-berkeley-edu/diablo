<template>
  <div>
    <h1>Your {{ $config.currentTermName }} courses</h1>
    <v-data-table
      :headers="headers"
      :hide-default-footer="true"
      :items="showEligibleCoursesOnly ? coursesEligibleOnly : courses"
      :items-per-page="100"
      :loading="loading"
      class="elevation-1"
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
      <template v-slot:body="{ items }">
        <tbody>
          <tr v-for="item in items" :key="item.name">
            <td>
              <div v-if="item.isEligible">
                <v-btn
                  :id="`sign-up-${item.sectionId}`"
                  :aria-label="`Sign ${item.course} up for Course Capture.`"
                  color="primary"
                  fab
                  small
                  dark
                  @click="goSignUp(item.sectionId)">
                  <v-icon>mdi-video-plus</v-icon>
                </v-btn>
              </div>
            </td>
            <td class="text-no-wrap">{{ item.course }}</td>
            <td>{{ item.title }}</td>
            <td>{{ item.instructors }}</td>
            <td class="text-no-wrap">{{ item.location }}</td>
            <td class="text-no-wrap">{{ item.days }}</td>
            <td class="text-no-wrap">{{ item.time }}</td>
          </tr>
        </tbody>
      </template>
    </v-data-table>
  </div>
</template>

<script>
  import Utils from '@/mixins/Utils'
  import router from '@/router'

  export default {
    name: 'Home',
    mixins: [Utils],
    data: () => ({
      courses: undefined,
      coursesEligibleOnly: undefined,
      headers: [
        {text: '', value: 'signUp'},
        {text: 'Course', value: 'course'},
        {text: 'Title', value: 'title'},
        {text: 'Instructors', value: 'instructors', sortable: false},
        {text: 'Location', value: 'location'},
        {text: 'Days', value: 'days', sortable: false},
        {text: 'Time', value: 'time', sortable: false}
      ],
      loading: true,
      showEligibleCoursesOnly: false
    }),
    created() {
      this.courses = []
      this.coursesEligibleOnly = []
      this.$_.each(this.$currentUser.teachingSections, s => {
        const isEligible = s.isEligibleForCourseCapture
        let course = {
          course: `${s.courseName}, ${s.instructionFormat} ${s.sectionNum}`,
          days: s.meetingDays ? this.$_.join(s.meetingDays, ', ') : undefined,
          instructors: this.oxfordJoin(this.$_.map(s.instructors, 'name')),
          isEligible,
          location: s.meetingLocation,
          sectionId: s.sectionId,
          time: s.meetingStartTime ? `${s.meetingStartTime} - ${s.meetingEndTime}` : undefined,
          title: s.courseTitle
        }
        this.courses.push(course)
        if (isEligible) {
          this.coursesEligibleOnly.push(course)
        }
      })
      this.loading = false
    },
    methods: {
      goSignUp(sectionId) {
        router.push({ path: `/course/${this.$config.currentTermId}/${sectionId}` })
      }
    }
  }
</script>
