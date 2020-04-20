<template>
  <div v-if="!loading">
    <h2>Your {{ $config.currentTermName }} courses</h2>
    <v-data-table
      disable-pagination
      :headers="headers"
      :hide-default-footer="true"
      :items="showEligibleCoursesOnly ? courses.eligibleOnly : courses.all"
      :items-per-page="100"
      class="elevation-1"
    >
      <template v-slot:top>
        <div v-if="courses.eligibleOnly.length" class="d-flex">
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
        <div v-if="!courses.eligibleOnly.length" class="pa-5">
          No courses eligible for Course Capture.
        </div>
      </template>
      <template v-slot:body="{ items }">
        <tbody>
          <tr v-for="item in items" :id="`course-${item.sectionId}`" :key="item.name">
            <td>
              <div v-if="item.room && item.room.capability">
                <v-btn
                  :id="`approve-${item.sectionId}`"
                  :aria-label="`Approve ${item.name} up for Course Capture.`"
                  color="primary"
                  fab
                  small
                  dark
                  @click="goApprove(item.sectionId)">
                  <v-icon>mdi-video-plus</v-icon>
                </v-btn>
              </div>
            </td>
            <td class="text-no-wrap">{{ item.name }}</td>
            <td>{{ item.title }}</td>
            <td>{{ item.instructors }}</td>
            <td class="text-no-wrap">{{ item.room ? item.room.location : '&mdash;' }}</td>
            <td class="text-no-wrap">{{ item.days }}</td>
            <td class="text-no-wrap">{{ item.time }}</td>
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
      courses: undefined,
      headers: [
        {text: '', value: 'approve'},
        {text: 'Course', value: 'name'},
        {text: 'Title', value: 'title'},
        {text: 'Instructors', value: 'instructors', sortable: false},
        {text: 'Room', value: 'room'},
        {text: 'Days', value: 'days', sortable: false},
        {text: 'Time', value: 'time', sortable: false}
      ],
      showEligibleCoursesOnly: false
    }),
    created() {
      this.$loading()
      this.courses = {
        all: [],
        eligibleOnly: []
      }
      this.$_.each(this.$currentUser.courses, c => {
        let course = {
          name: c.label,
          days: c.meetingDays ? this.$_.join(c.meetingDays, ', ') : undefined,
          instructors: this.oxfordJoin(this.$_.map(c.instructors, 'name')),
          room: c.room,
          sectionId: c.sectionId,
          time: c.meetingStartTime ? `${c.meetingStartTime} - ${c.meetingEndTime}` : undefined,
          title: c.courseTitle
        }
        this.courses['all'].push(course)
        if (c.room && c.room.capability) {
          this.courses['eligibleOnly'].push(course)
        }
      })
      this.$ready()
    },
    methods: {
      goApprove(sectionId) {
        router.push({ path: `/approve/${this.$config.currentTermId}/${sectionId}` })
      }
    }
  }
</script>
