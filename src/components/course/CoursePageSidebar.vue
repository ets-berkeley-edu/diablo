<template>
  <v-container class="elevation-2 pa-6">
    <h2 class="sr-only">Summary of {{ course.label }} course</h2>
    <v-row v-if="instructors.length" id="instructors" :class="{'line-through': course.deletedAt}">
      <v-col md="auto">
        <h3 class="sr-only">Instructors</h3>
        <v-icon aria-label="Mortarboard icon">mdi-school-outline</v-icon>
      </v-col>
      <v-col>
        <OxfordJoin v-slot="{item}" :items="instructors">
          <router-link
            v-if="$currentUser.isAdmin"
            :id="`instructor-sidebar-link-${item.uid}`"
            aria-label="Link to instructor page"
            :to="`/user/${item.uid}`"
          >
            {{ item.name }}
          </router-link>
          <span v-if="!$currentUser.isAdmin" :id="`instructor-${item.uid}`">{{ item.name }}</span>
          <span v-if="item.roleCode === 'APRX'" :id="`instructor-${item.uid}-is-proxy`"> (administrative proxy)</span>
        </OxfordJoin>
        <div v-if="instructorProxies.length" class="text--secondary subtitle-2">
          (<OxfordJoin v-slot="{item}" :items="instructorProxies">
            <span :id="`instructor-proxy-${item.uid}`">{{ item.name }}</span>
          </OxfordJoin>
          {{ instructorProxies.length === 1 ? 'is an Admin Proxy' : 'are Admin Proxies' }}.)
        </div>
      </v-col>
    </v-row>
    <div v-for="(meeting, index) in displayMeetings" :key="index">
      <h3 class="sr-only">Meeting {{ displayMeetings.length > 1 ? `#${index}` : '' }}</h3>
      <v-row v-if="meeting.daysNames" :id="`meeting-days-${index}`" :class="{'line-through': course.deletedAt}">
        <v-col md="auto" :class="{'pb-0': displayMeetings.length > 1}">
          <v-icon aria-label="Calendar icon">mdi-calendar</v-icon>
        </v-col>
        <v-col :class="{'pb-0': displayMeetings.length > 1}">
          <Days :names-of-days="meeting.daysNames" />
          <div>
            <span class="sr-only">Dates:</span>
            {{ meeting.startDate | moment('MMM D, YYYY') }} to {{ meeting.endDate | moment('MMM D, YYYY') }}
            <div v-if="course.scheduled && !course.hasOptedOut && meeting.recordingEndDate && meeting.endDate !== meeting.recordingEndDate" class="font-weight-light">
              <div v-if="course.termId === $config.currentTermId">
                (Final recording
                <span v-if="meeting.recordingEndDate < nowDate">was on</span>
                <span v-if="meeting.recordingEndDate > nowDate">scheduled for</span>
                <span v-if="meeting.recordingEndDate === nowDate">is today, </span>
                {{ meeting.recordingEndDate | moment('MMM D, YYYY') }}.)
              </div>
              <div v-if="course.termId < $config.currentTermId">
                (Final recording was on {{ meeting.recordingEndDate | moment('MMM D, YYYY') }}.)
              </div>
            </div>
          </div>
        </v-col>
      </v-row>
      <v-row v-if="meeting.startTimeFormatted" :id="`meeting-times-${index}`" :class="{'line-through': course.deletedAt}">
        <v-col md="auto" :class="{'pb-1 pt-1': displayMeetings.length > 1}">
          <v-icon aria-label="Clock icon">mdi-clock-outline</v-icon>
        </v-col>
        <v-col :class="{'pb-1 pt-1': displayMeetings.length > 1}">
          <span class="sr-only">Start and end times:</span>
          {{ meeting.startTimeFormatted }} - {{ meeting.endTimeFormatted }}
        </v-col>
      </v-row>
      <v-row v-if="meeting.room" :id="`rooms-${index}`" :class="{'line-through': course.deletedAt}">
        <v-col md="auto" :class="{'pb-5 pt-1': displayMeetings.length > 1}">
          <v-icon aria-label="Map icon">mdi-map-marker</v-icon>
        </v-col>
        <v-col v-if="$currentUser.isAdmin" :class="{'pb-5 pt-1': displayMeetings.length > 1}">
          <router-link
            id="room"
            aria-label="Link to room page"
            :to="`/room/${meeting.room.id}`"
          >
            {{ meeting.room.location }}
          </router-link>
        </v-col>
        <v-col v-if="!$currentUser.isAdmin">
          <span class="sr-only">Location: </span>{{ meeting.room.location }}
        </v-col>
      </v-row>
    </div>
    <v-row v-if="course.crossListings.length" id="cross-listings">
      <v-col md="auto">
        <v-icon aria-label="List icon">mdi-format-line-spacing</v-icon>
      </v-col>
      <v-col>
        <span>Cross-listing<span v-if="course.crossListings.length !== 1">s</span></span>
        <div
          v-for="crossListing in course.crossListings"
          :id="`cross-listing-${crossListing.sectionId}`"
          :key="crossListing.sectionId"
        >
          {{ crossListing.label }}
        </div>
      </v-col>
    </v-row>
    <v-row v-if="$currentUser.isAdmin && course.hasOptedOut" id="opted-out">
      <v-col md="auto">
        <v-icon aria-label="'Do not disturb' icon">mdi-minus-circle</v-icon>
      </v-col>
      <v-col>
        Opted out
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import Context from '@/mixins/Context'
import Days from '@/components/util/Days'
import OxfordJoin from '@/components/util/OxfordJoin'
import Utils from '@/mixins/Utils'

export default {
  name: 'CoursePageSidebar',
  components: {Days, OxfordJoin},
  mixins: [Context, Utils],
  props: {
    course: {
      required: true,
      type: Object
    }
  },
  data: () => ({
    displayMeetings: undefined,
    instructors: undefined,
    instructorProxies: undefined,
    nowDate: undefined,
  }),
  created() {
    this.displayMeetings = this.getDisplayMeetings(this.course)
    this.instructors = this.$_.filter(this.course.instructors, i => i.roleCode !== 'APRX')
    this.instructorProxies = this.$_.filter(this.course.instructors, i => i.roleCode === 'APRX')
    this.nowDate = this.$moment().format('YYYY-MM-DD')
  }
}
</script>
