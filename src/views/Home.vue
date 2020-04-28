<template>
  <div v-if="!loading">
    <div class="pb-3">
      <h1>Your {{ $config.currentTermName }} Courses Eligible for Capture</h1>
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
          <tr v-for="course in items" :id="`course-${course.sectionId}`" :key="course.sectionId">
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

  export default {
    name: 'Home',
    mixins: [Context, Utils],
    data: () => ({
      courses: undefined,
      headers: [
        {text: 'Course', value: 'label'},
        {text: 'Title', value: 'title'},
        {text: 'Instructors', value: 'instructors', sortable: false},
        {text: 'Room', value: 'room'},
        {text: 'Days', value: 'days', sortable: false},
        {text: 'Time', value: 'time', sortable: false}
      ]
    }),
    created() {
      this.$loading()
      this.courses = []
      this.$_.each(this.$currentUser.courses, c => {
        if (c.room && c.room.capability) {
          this.courses.push({
            label: c.label,
            days: c.meetingDays ? this.$_.join(c.meetingDays, ', ') : undefined,
            instructors: this.oxfordJoin(this.$_.map(c.instructors, 'name')),
            room: c.room,
            sectionId: c.sectionId,
            time: c.meetingStartTime ? `${c.meetingStartTime} - ${c.meetingEndTime}` : undefined,
            title: c.courseTitle
          })
        }
      })
      this.$ready()
    }
  }
</script>
