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
          <tr v-for="course in items" :id="`course-${course.sectionId}`" :key="course.sectionId">
            <td class="text-no-wrap" :class="{'pt-3 pb-3': course.courseCodes.length > 1}">
              <div v-if="course.room && course.room.capability">
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
      ],
      pageTitle: undefined
    }),
    created() {
      this.$loading()
      this.pageTitle = `Your ${this.$config.currentTermName} Courses Eligible for Capture`
      this.courses = []
      this.$_.each(this.$currentUser.courses, c => {
        this.$_each(c.meetings, m => {
          if (m.room && m.room.capability) {
            this.courses.push({
              courseCodes: this.getCourseCodes(c),
              days: m.daysFormatted ? this.$_.join(c.daysFormatted, ', ') : undefined,
              instructors: this.oxfordJoin(this.$_.map(c.instructors, 'name')),
              room: m.room,
              sectionId: c.sectionId,
              time: m.startTimeFormatted ? `${m.startTimeFormatted} - ${m.endTimeFormatted}` : undefined,
              title: c.courseTitle
            })
          }
        })
      })
      this.$ready(this.pageTitle)
    }
  }
</script>
