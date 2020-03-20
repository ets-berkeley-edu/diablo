<template>
  <div>
    <div class="pl-3">
      <h2><v-icon class="pb-3" large>mdi-auto-fix</v-icon> The Ouija Board</h2>
    </div>
    <v-card flat outlined :class="overrideVuetify($vuetify.theme, 'v-card--outlined')">
      <v-card-title>
        Courses
        <v-spacer></v-spacer>
        <v-text-field
          v-model="search"
          append-icon="mdi-magnify"
          label="Search"
          single-line
          hide-details
        ></v-text-field>
      </v-card-title>
      <v-data-table
        :headers="headers"
        :items="courses"
        :search="search"
      >
        <template v-slot:body="{ items }">
          <tbody>
            <tr v-if="!items.length">
              <td>
                <div v-if="search">
                  No matching items
                </div>
                <div v-if="!search">
                  No courses
                </div>
              </td>
            </tr>
            <tr v-for="item in items" :key="item.name">
              <td class="text-no-wrap">{{ item.sectionId }}</td>
              <td class="text-no-wrap">{{ item.room.location }}</td>
              <td class="text-no-wrap">{{ item.meetingDays.join(',') }}</td>
              <td class="text-no-wrap">{{ item.meetingStartTime }} - {{ item.meetingEndTime }}</td>
              <td>
                <span v-for="instructor in item.instructors" :key="instructor.uid">
                  <a
                    :id="`instructor-${instructor.uid}-mailto`"
                    :href="`mailto:${instructor.campusEmail}`"
                    target="_blank">
                    {{ instructor.name }}
                  </a>
                </span>
              </td>
              <td>
                <span>
                  {{ $_.last(item.approvals).publishTypeName }}
                </span>
              </td>
            </tr>
          </tbody>
        </template>
      </v-data-table>
    </v-card>
  </div>
</template>

<script>
  import Utils from '@/mixins/Utils'
  import {getTermSummary} from '@/api/report'

  export default {
    name: 'Ouija',
    mixins: [Utils],
    data: () => ({
      courses: undefined,
      search: '',
      headers: [
        {text: 'Course', value: 'courseName'},
        {text: 'Section', value: 'sectionId'},
        {text: 'Room', value: 'room.location'},
        {text: 'Days', value: 'days', sortable: false},
        {text: 'Time', value: 'time', sortable: false},
        {text: 'Instructor(s)', value: 'instructorNames'},
        {text: 'Recording', value: 'recording', sortable: false}
      ]
    }),
    created() {
      getTermSummary(this.$config.currentTermId).then(data => {
        this.courses = data
        this.$ready()
      })
    }
  }
</script>
