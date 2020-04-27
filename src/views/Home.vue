<template>
  <div v-if="!loading">
    <div class="pb-3">
      <h2>Your {{ $config.currentTermName }} courses</h2>
    </div>
    <v-data-table
      disable-pagination
      :headers="headers"
      :hide-default-footer="true"
      :items="courses"
      :items-per-page="100"
      class="elevation-1"
    >
      <template v-slot:top>
        <div v-if="eligibleCourses.length && eligibleCourses.length < allCourses.length" class="d-flex">
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
        <div v-if="!eligibleCourses.length" class="pa-5">
          No courses eligible for Course Capture.
        </div>
      </template>
      <template v-slot:body="{ items }">
        <tbody>
          <tr v-for="course in items" :id="`course-${course.sectionId}`" :key="course.sectionId">
            <td>
              <div v-if="course.room && course.room.capability">
                <v-btn
                  :id="`btn-course-${course.sectionId}`"
                  :aria-label="`Go to ${course.label} page`"
                  color="primary"
                  fab
                  small
                  dark
                  @click="visitCourse(course.sectionId)">
                  <v-icon>mdi-video-plus</v-icon>
                </v-btn>
              </div>
            </td>
            <td class="text-no-wrap">
              <div v-if="course.room && course.room.capability">
                <router-link
                  v-if="course.room && course.room.capability"
                  :id="`link-course-${course.sectionId}`"
                  :aria-label="`Go to ${course.label} page`"
                  :to="`/course/${$config.currentTermId}/${course.sectionId}`">
                  {{ course.label }}
                </router-link>
              </div>
              <span v-if="!course.room || !course.room.capability">{{ course.label }}</span>
            </td>
            <td>{{ course.title }}</td>
            <td>{{ course.instructors }}</td>
            <td class="text-no-wrap">{{ course.room ? course.room.location : '&mdash;' }}</td>
            <td class="text-no-wrap">{{ course.days }}</td>
            <td class="text-no-wrap">{{ course.time }}</td>
          </tr>
        </tbody>
      </template>
    </v-data-table>
  </div>
</template>

<script>
  import Context from '@/mixins/Context'
  import Utils from '@/mixins/Utils'
  import router from '@/router'

  export default {
    name: 'Home',
    mixins: [Context, Utils],
    data: () => ({
      allCourses: undefined,
      eligibleCourses: undefined,
      headers: [
        {text: '', value: 'approve'},
        {text: 'Course', value: 'label'},
        {text: 'Title', value: 'title'},
        {text: 'Instructors', value: 'instructors', sortable: false},
        {text: 'Room', value: 'room'},
        {text: 'Days', value: 'days', sortable: false},
        {text: 'Time', value: 'time', sortable: false}
      ],
      showEligibleCoursesOnly: false
    }),
    computed: {
      courses() {
        return this.showEligibleCoursesOnly ? this.eligibleCourses : this.allCourses
      }
    },
    created() {
      this.$loading()
      this.allCourses = []
      this.eligibleCourses = []
      this.$_.each(this.$currentUser.courses, c => {
        let course = {
          label: c.label,
          days: c.meetingDays ? this.$_.join(c.meetingDays, ', ') : undefined,
          instructors: this.oxfordJoin(this.$_.map(c.instructors, 'name')),
          room: c.room,
          sectionId: c.sectionId,
          time: c.meetingStartTime ? `${c.meetingStartTime} - ${c.meetingEndTime}` : undefined,
          title: c.courseTitle
        }
        this.allCourses.push(course)
        if (c.room && c.room.capability) {
          this.eligibleCourses.push(course)
        }
      })
      this.$ready()
    },
    methods: {
      visitCourse(sectionId) {
        router.push({ path: `/course/${this.$config.currentTermId}/${sectionId}` })
      }
    }
  }
</script>
