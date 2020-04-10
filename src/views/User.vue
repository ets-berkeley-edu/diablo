<template>
  <div v-if="!loading">
    <h2>{{ user.name }} ({{ user.uid }})</h2>
    <div class="pb-3">
      <a :href="`mailto:${user.campusEmail}`" target="_blank">{{ user.campusEmail }}<span class="sr-only"> (new browser tab will open)</span></a>
    </div>
    <v-card outlined class="elevation-1">
      <v-card-title>
        Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
      </v-card-title>
      <v-data-table
        disable-pagination
        hide-default-footer
        :headers="headers"
        :items="user.courses"
      >
        <template v-slot:body="{ items }">
          <tbody v-if="items.length">
            <template v-for="item in items">
              <tr :key="item.sectionId">
                <td :class="tdClass(item)">
                  <router-link
                    v-if="item.room.capability"
                    :id="`sign-up-${item.sectionId}`"
                    class="subtitle-1"
                    :to="`/approve/${$config.currentTermId}/${item.sectionId}`">
                    <v-icon class="mb-1">mdi-video-plus</v-icon> {{ item.courseName }}
                  </router-link>
                  <span v-if="!item.room.capability">{{ item.courseName }}</span>
                </td>
                <td :class="tdClass(item)">{{ item.sectionId }}</td>
                <td :class="tdClass(item)">
                  <router-link
                    v-if="item.room"
                    :id="`course-${item.sectionId}-room-${item.room.id}`"
                    :to="`/room/${item.room.id}`">
                    {{ item.room.location }}
                  </router-link>
                  <span v-if="!item.room">&nbsp;</span>
                </td>
                <td :class="tdClass(item)">{{ item.meetingDays ? item.meetingDays.join(',') : '&mdash;' }}</td>
                <td :class="tdClass(item)">{{ item.meetingStartTime ? `${item.meetingStartTime} - ${item.meetingEndTime}` : '&mdash;' }}</td>
                <td :class="tdClass(item)">
                  {{ item.publishTypeNames || '&mdash;' }}
                </td>
                <td :class="tdClass(item)">
                  <ToggleOptOut :key="item.sectionId" :course="item" />
                </td>
              </tr>
              <tr v-if="item.approvals.length" :key="`approvals-${item.sectionId}`">
                <td colspan="7" class="pb-2">
                  <div v-if="item.approvals.length === 1">
                    "{{ item.approvals[0].recordingTypeName }}" recording was approved for "{{ item.approvals[0].publishTypeName }}" by
                    <router-link :id="`instructor-${item.approvals[0].approvedBy.uid}-mailto`" :to="`/user/${item.approvals[0].approvedBy.uid}`">
                      {{ item.approvals[0].approvedBy.name }}
                    </router-link> ({{ item.approvals[0].approvedBy.uid }}) on {{ item.approvals[0].createdAt | moment('MMM D, YYYY') }}.
                  </div>
                  <div v-if="item.approvals.length > 1">
                    <h3>Approvals</h3>
                  </div>
                </td>
              </tr>
            </template>
          </tbody>
          <tbody v-if="!items.length">
            <tr>
              <td>
                No courses
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
  import {getUser} from '@/api/user'

  export default {
    name: 'Room',
    components: {ToggleOptOut},
    mixins: [Context, Utils],
    data: () => ({
      user: undefined,
      headers: [
        {text: 'Course', value: 'courseName'},
        {text: 'Section', value: 'sectionId'},
        {text: 'Room', value: 'room.location'},
        {text: 'Days', value: 'days', sortable: false},
        {text: 'Time', value: 'time', sortable: false},
        {text: 'Publish', value: 'publishTypeNames'},
        {text: 'Opt out', value: 'hasOptedOut', sortable: false}
      ]
    }),
    created() {
      this.$loading()
      let uid = this.$_.get(this.$route, 'params.uid')
      getUser(uid).then(user => {
        this.user = user
        this.setPageTitle(this.user.name)
        this.$_.each(this.user.courses, course => {
          // In support of search, we index nested course data
          course.instructorNames = this.$_.map(course.instructors, 'name')
          course.publishTypeNames = course.approvals.length ? this.$_.last(course.approvals).publishTypeName : null
          course.isSelectable = !course.hasOptedOut
        })
        this.$ready()
      }).catch(this.$ready)
    },
    methods: {
      tdClass(item) {
        return item.approvals.length ? 'border-bottom-zero text-no-wrap' : 'text-no-wrap'
      }
    }
  }
</script>

<style scoped>
  .border-bottom-zero {
    border-bottom: 0 !important;
  }
</style>
