<template>
  <div v-if="!loading">
    <div class="pb-3">
      <h2><v-icon class="pb-3" large>mdi-auto-fix</v-icon> The Ouija Board</h2>
    </div>
    <v-card outlined class="elevation-1">
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
      <div class="pl-5">
        <v-btn :disabled="!selected.length" small>Send Email</v-btn>
        <v-checkbox
          :input-value="emailAll"
          :true-value="emailAll"
          :indeterminate="emailSome"
          label="Email all"
          @click.capture.stop="toggleEmailAll"
        ></v-checkbox>
      </div>
      <v-data-table
        hide-default-footer
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
              <td class="text-no-wrap">
                <v-checkbox
                  v-model="selected"
                  :true-value="$_.includes(selected, item.sectionId)"
                  :value="item.sectionId"></v-checkbox>
              </td>
              <td class="text-no-wrap">{{ item.courseName }}</td>
              <td class="text-no-wrap">{{ item.sectionId }}</td>
              <td class="text-no-wrap">
                <router-link
                  v-if="item.room"
                  :id="`course-${item.sectionId}-room-${item.room.id}`"
                  :to="`/room/${item.room.id}`">
                  {{ item.room.location }}
                </router-link>
                <span v-if="!item.room">&nbsp;</span>
              </td>
              <td class="text-no-wrap">{{ item.meetingDays.join(',') }}</td>
              <td class="text-no-wrap">{{ item.meetingStartTime }} - {{ item.meetingEndTime }}</td>
              <td>
                <div v-for="instructor in item.instructors" :key="instructor.uid">
                  <router-link :id="`instructor-${instructor.uid}-mailto`" :to="`/user/${instructor.uid}`">
                    {{ instructor.name }}
                  </router-link> ({{ instructor.uid }})
                </div>
              </td>
              <td>
                <span>
                  {{ $_.last(item.approvals).publishTypeName }}
                </span>
              </td>
              <td>
                <ToggleOptOut :course="item" />
              </td>
            </tr>
          </tbody>
        </template>
      </v-data-table>
    </v-card>
  </div>
</template>

<script>
  import Context from '@/mixins/Context'
  import ToggleOptOut from '@/components/course/ToggleOptOut'
  import Utils from '@/mixins/Utils'
  import {getTermSummary} from '@/api/course'

  export default {
    name: 'Ouija',
    components: {ToggleOptOut},
    mixins: [Context, Utils],
    data: () => ({
      courses: undefined,
      headers: [
        {text: '', sortable: false},
        {text: 'Course', value: 'courseName'},
        {text: 'Section', value: 'sectionId'},
        {text: 'Room', value: 'room.location'},
        {text: 'Days', value: 'days', sortable: false},
        {text: 'Time', value: 'time', sortable: false},
        {text: 'Instructor(s)', value: 'instructorNames'},
        {text: 'Recording', value: 'recording', sortable: false},
        {text: 'Opt out', value: 'hasOptedOut'}
      ],
      search: '',
      selected: undefined
    }),
    computed: {
      emailAll() {
        return this.selected.length === this.courses.length
      },
      emailSome() {
        return this.selected.length > 0 && !this.emailAll
      }
    },
    created() {
      this.$loading()
      getTermSummary(this.$config.currentTermId).then(data => {
        this.courses = data
        this.selected = this.$_.map(this.courses, 'sectionId')
        this.$ready()
      }).catch(this.$ready)
    },
    methods: {
      toggleEmailAll() {
        this.selected = this.emailAll ? [] : this.$_.map(this.courses, 'sectionId')
      }
    }
  }
</script>
