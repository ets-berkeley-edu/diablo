<template>
  <v-card
    aria-labelledby="course-page-sidebar-title"
    class="pa-6"
    outlined
    tile
  >
    <h2 id="course-page-sidebar-title" class="sr-only">Summary of {{ course.label }} course</h2>
    <v-row v-if="course.instructors.length" id="instructors">
      <v-col md="auto">
        <h3 class="sr-only">Instructors</h3>
        <v-icon aria-label="Mortarboard icon">mdi-school-outline</v-icon>
      </v-col>
      <v-col>
        <OxfordJoin v-slot="{ item }" :items="course.instructors">
          <router-link
            v-if="$currentUser.isAdmin"
            :id="`instructor-${item.uid}`"
            aria-label="Link to instructor page"
            :to="`/user/${item.uid}`"
          >
            {{ item.name }}
          </router-link>
          <span v-if="!$currentUser.isAdmin" :id="`instructor-${item.uid}`">{{ item.name }}</span>
        </OxfordJoin>
      </v-col>
    </v-row>
    <div v-for="(meeting, index) in displayMeetings" :key="index">
      <h3 class="sr-only">Meeting {{ displayMeetings.length > 1 ? `#${index}` : '' }}</h3>
      <v-row v-if="meeting.daysNames" :id="`meeting-days-${index}`">
        <v-col md="auto" :class="{'pb-0': displayMeetings.length > 1}">
          <v-icon aria-label="Calendar icon">mdi-calendar</v-icon>
        </v-col>
        <v-col :class="{'pb-0': displayMeetings.length > 1}">
          <Days :names-of-days="meeting.daysNames" />
          <div>
            <span class="sr-only">Dates:</span>
            {{ meeting.startDate | moment('MMM D, YYYY') }} to {{ meeting.endDate | moment('MMM D, YYYY') }}
            <div v-if="meeting.recordingEndDate && meeting.endDate !== meeting.recordingEndDate" class="font-weight-light">
              <div v-if="course.termId === $config.currentTermId">
                (Final recording
                <span v-if="meeting.recordingEndDate < nowDate">was on</span>
                <span v-if="meeting.recordingEndDate > nowDate">scheduled for</span>
                <span v-if="meeting.recordingEndDate === nowDate">is today, </span>
                {{ meeting.recordingEndDate | moment('MMM D, YYYY') }}.)
              </div>
              <div v-if="course.termId < $config.currentTermId && course.scheduled">
                (Final recording was on {{ meeting.recordingEndDate | moment('MMM D, YYYY') }}.)
              </div>
            </div>
          </div>
        </v-col>
      </v-row>
      <v-row v-if="meeting.startTimeFormatted" :id="`meeting-times-${index}`">
        <v-col md="auto" :class="{'pb-1 pt-1': displayMeetings.length > 1}">
          <v-icon aria-label="Clock icon">mdi-clock-outline</v-icon>
        </v-col>
        <v-col :class="{'pb-1 pt-1': displayMeetings.length > 1}">
          <span class="sr-only">Start and end times:</span>
          {{ meeting.startTimeFormatted }} - {{ meeting.endTimeFormatted }}
        </v-col>
      </v-row>
      <v-row v-if="meeting.room" :id="`rooms-${index}`">
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
    <v-row v-if="course.canvasCourseSites.length" id="canvas-course-sites">
      <v-col md="auto">
        <v-icon aria-label="Bookmark icon">mdi-bookmark-outline</v-icon>
      </v-col>
      <v-col>
        <OxfordJoin v-slot="{ item }" :items="course.canvasCourseSites">
          <CanvasCourseSite :site="item" />
        </OxfordJoin>
      </v-col>
    </v-row>
    <v-row v-if="$currentUser.isAdmin && course.hasOptedOut" id="opted-out">
      <v-col md="auto">
        <v-icon aria-label="'Do not disturb' icon">mdi-do-not-disturb</v-icon>
      </v-col>
      <v-col>
        Opted out
      </v-col>
    </v-row>
    <v-row
      v-if="offerSendInvite"
      id="send-invite"
      justify="center"
      class="mt-2"
    >
      <v-btn
        id="send-invite-btn"
        @click="sendInvite"
      >
        Send Invite
      </v-btn>
    </v-row>
    <v-row v-if="offerUnschedule" id="unschedule" justify="center">
      <v-col md="auto">
        <v-dialog v-model="showUnscheduleModal" persistent max-width="400">
          <template v-slot:activator="{ on, attrs }">
            <v-btn
              id="unschedule-course-btn"
              color="primary"
              v-bind="attrs"
              v-on="on"
            >
              Unschedule
            </v-btn>
          </template>
          <v-card>
            <v-card-title class="headline">Unschedule this course?</v-card-title>
            <v-card-text>
              The schedule and approvals for this course will be removed from Diablo,
              the Kaltura series will be deleted,
              and the course will be marked as opt-out.
            </v-card-text>
            <v-card-actions>
              <v-spacer></v-spacer>
              <v-btn
                id="confirm-unschedule-course-btn"
                color="blue"
                text
                @click="unscheduleCourse"
              >
                Confirm
              </v-btn>
              <v-btn
                id="cancel-unschedule-course-btn"
                color="blue"
                text
                @click="showUnscheduleModal = false"
              >
                Cancel
              </v-btn>
            </v-card-actions>
          </v-card>
        </v-dialog>
      </v-col>
    </v-row>
  </v-card>
</template>

<script>
  import CanvasCourseSite from '@/components/course/CanvasCourseSite'
  import Context from '@/mixins/Context'
  import Days from '@/components/util/Days'
  import OxfordJoin from '@/components/util/OxfordJoin'
  import Utils from '@/mixins/Utils'
  import {unschedule} from '@/api/course'
  import {queueEmail} from '@/api/email'

  export default {
    name: 'CoursePageSidebar',
    components: {CanvasCourseSite, Days, OxfordJoin},
    mixins: [Context, Utils],
    props: {
      afterUnschedule: {
        required: true,
        type: Function
      },
      course: {
        required: true,
        type: Object
      }
    },
    data: () => ({
      displayMeetings: undefined,
      nowDate: undefined,
      showUnscheduleModal: false
    }),
    computed: {
      offerSendInvite() {
        return this.$currentUser.isAdmin
          && this.course.termId === this.$config.currentTermId
          && this.course.instructors.length
          && !this.course.hasOptedOut
          && this.course.meetings.eligible.length === 1
      },
      offerUnschedule() {
        return this.$currentUser.isAdmin
          && this.course.termId === this.$config.currentTermId
          && (this.course.scheduled || this.course.hasNecessaryApprovals)
      }
    },
    created() {
      this.displayMeetings = this.getDisplayMeetings(this.course)
      this.nowDate = this.$moment().format('YYYY-MM-DD')
    },
    methods: {
      sendInvite() {
        queueEmail('invitation', this.course.sectionId, this.course.termId).then(data => {
          this.snackbarOpen(data.message)
        })
      },
      unscheduleCourse() {
        this.$loading()
        this.showUnscheduleModal = false
        unschedule(this.course.termId, this.course.sectionId).then(data => {
          this.alertScreenReader(`${this.course.label} unscheduled.`)
          this.afterUnschedule(data)
        })
      }
    }
  }
</script>
