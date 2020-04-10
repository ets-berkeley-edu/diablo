<template>
  <v-card v-if="!loading" outlined class="elevation-1">
    <v-card-title class="align-start">
      <div class="pt-2">
        <h2><v-icon class="pb-3" large>mdi-swap-horizontal</v-icon> Course Changes</h2>
      </div>
    </v-card-title>
    <v-data-table
      disable-pagination
      :headers="headers"
      hide-default-footer
      item-key="sectionId"
      :items="courses"
    >
      <template v-slot:body="{ items }">
        <tbody>
          <tr v-if="!items.length">
            <td colspan="10">
              <div class="ma-4 text-no-wrap title">
                No changes for courses invited to Course Capture.
              </div>
            </td>
          </tr>
          <tr v-for="item in items" :key="item.courseName">
            <td class="pa-3 text-no-wrap">
              <div class="font-weight-black">
                {{ item.courseName }}
              </div>
              <div>
                {{ item.sectionId }}
              </div>
              <div>
                {{ item.meetingDays.join(',') }}
              </div>
              <div>
                {{ item.meetingStartTime }} - {{ item.meetingEndTime }}
              </div>
              <div>
                {{ item.publishTypeNames }}
              </div>
            </td>
            <td class="text-no-wrap">
              <div v-for="roomBefore in item.roomsBefore" :key="roomBefore">
                <div>
                  <router-link
                    :id="`course-${item.sectionId}-room-before-${roomBefore.id}`"
                    :to="`/room/${roomBefore.id}`">
                    {{ roomBefore.location }}
                  </router-link>
                </div>
                <div>
                  <v-icon small>mdi-arrow-down-bold</v-icon>
                  changed to
                </div>
              </div>
              <router-link
                v-if="item.room"
                :id="`course-${item.sectionId}-room-${item.room.id}`"
                :to="`/room/${item.room.id}`">
                {{ item.room.location }}
              </router-link>
              <span v-if="!item.room">&mdash;</span>
            </td>
            <td>
              <div v-for="instructor in item.instructors" :key="instructor.uid">
                <router-link :id="`instructor-${instructor.uid}-mailto`" :to="`/user/${instructor.uid}`">
                  {{ instructor.name }}
                </router-link> ({{ instructor.uid }})
              </div>
            </td>
          </tr>
        </tbody>
      </template>
    </v-data-table>
  </v-card>
</template>

<script>
  import Context from '@/mixins/Context'
  import {getCourseChanges} from '@/api/course'

  export default {
    name: 'CourseChanges',
    mixins: [Context],
    data: () => ({
      courses: undefined,
      headers: [
        {text: 'Course Information', value: 'courseName'},
        {text: 'Room', value: 'meetingLocation'},
        {text: 'Instructor(s)', value: 'instructorNames', sortable: false}
      ]
    }),
    created() {
      this.$loading()
      getCourseChanges(this.$config.currentTermId).then(data => {
        this.courses = []
        this.$_.each(data, course => {
          course.roomsBefore = []
          this.$_.each([course.approvals, course.scheduled], actions => {
            this.$_.each(this.$_.filter(actions, 'isObsolete'), obsolete => {
              if (!this.$_.includes(course.roomsBefore, obsolete.room)) {
                course.roomsBefore.push(obsolete.room)
              }
            })
          })
          this.courses.push(course)
        })
        this.$ready()
      })
    }
  }
</script>
