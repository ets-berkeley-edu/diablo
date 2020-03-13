<template>
  <div>
    <div class="pl-3">
      <h2><v-icon class="pb-3" large>mdi-auto-fix</v-icon> The Ouija Board</h2>
    </div>
    <v-data-table
      :headers="headers"
      :hide-default-footer="true"
      :items="sections"
      :items-per-page="100"
      :loading="loading"
      class="elevation-1"
    >
      <template v-slot:top>
        <div class="pa-3">
          Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
        </div>
      </template>
      <template v-slot:body="{ items }">
        <tbody>
          <tr v-for="item in items" :key="item.name">
            <td>{{ item.courseName }}</td>
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
  </div>
</template>

<script>
  import Loading from '@/mixins/Loading'
  import Utils from '@/mixins/Utils'
  import {getTermSummary} from '@/api/report'

  export default {
    name: 'Ouija',
    mixins: [Loading, Utils],
    data: () => ({
      sections: undefined,
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
        this.sections = data
        this.loaded()
      })
    }
  }
</script>
