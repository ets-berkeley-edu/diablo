<template>
  <v-card class="pa-6" outlined tile>
    <v-row v-if="course.instructors.length" id="instructors">
      <v-col md="auto">
        <v-icon>mdi-school-outline</v-icon>
      </v-col>
      <v-col>
        <OxfordJoin v-slot="{ item }" :items="course.instructors">
          <router-link v-if="$currentUser.isAdmin" :id="`instructor-${item.uid}`" :to="`/user/${item.uid}`">{{ item.name }}</router-link>
          <span v-if="!$currentUser.isAdmin" :id="`instructor-${item.uid}`">{{ item.name }}</span>
        </OxfordJoin>
      </v-col>
    </v-row>
    <v-row v-if="course.meetingDays" id="meeting-days">
      <v-col md="auto">
        <v-icon>mdi-calendar</v-icon>
      </v-col>
      <v-col>
        {{ $_.join(course.meetingDays, ', ') }}
      </v-col>
    </v-row>
    <v-row v-if="course.meetingStartTime" id="meeting-times">
      <v-col md="auto">
        <v-icon>mdi-clock-outline</v-icon>
      </v-col>
      <v-col>
        {{ course.meetingStartTime }} - {{ course.meetingEndTime }}
      </v-col>
    </v-row>
    <v-row v-if="course.room" id="rooms">
      <v-col md="auto">
        <v-icon>mdi-map-marker</v-icon>
      </v-col>
      <v-col v-if="$currentUser.isAdmin">
        <router-link id="room" :to="`/room/${course.room.id}`">{{ course.room.location }}</router-link>
      </v-col>
      <v-col v-if="!$currentUser.isAdmin">
        {{ course.room.location }}
      </v-col>
    </v-row>
    <v-row v-if="course.crossListings.length" id="cross-listings">
      <v-col md="auto">
        <v-icon>mdi-format-line-spacing</v-icon>
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
        <v-icon>mdi-bookmark-outline</v-icon>
      </v-col>
      <v-col>
        <span v-for="(canvasCourseSite, index) in course.canvasCourseSites" :key="canvasCourseSite.courseSiteId">
          <a
            :id="`canvas-course-site-${canvasCourseSite.courseSiteId}`"
            :href="`${$config.canvasBaseUrl}/courses/${canvasCourseSite.courseSiteId}`"
            target="_blank"
          >{{ canvasCourseSite.courseSiteName }}</a>
          <span v-if="course.canvasCourseSites.length > 1 && index === course.canvasCourseSites.length - 2"> and </span>
        </span>
      </v-col>
    </v-row>
    <v-row v-if="$currentUser.isAdmin && course.hasOptedOut" id="opted-out">
      <v-col md="auto">
        <v-icon>mdi-do-not-disturb</v-icon>
      </v-col>
      <v-col>
        Opted out
      </v-col>
    </v-row>
    <v-row
      v-if="$currentUser.isAdmin && course.room && course.room.capability && course.instructors.length"
      id="send-invite"
      justify="center"
      class="mt-2"
    >
      <v-btn
        id="send-invite-btn"
        @click="sendInvite()"
      >
        Send Invite
      </v-btn>
    </v-row>
    <v-row v-if="$currentUser.isAdmin && course.scheduled" id="unschedule" justify="center">
      <v-col md="auto">
        <v-dialog v-model="showUnscheduleModal" persistent max-width="400">
          <template v-slot:activator="{ on }">
            <v-btn
              id="unschedule-course-btn"
              color="primary"
              v-on="on"
            >
              Unschedule
            </v-btn>
          </template>
          <v-card>
            <v-card-title class="headline">Unschedule this course?</v-card-title>
            <v-card-text>The schedule and approvals for this course will be removed from Diablo, and the course will be marked as opt-out.</v-card-text>
            <v-card-actions>
              <v-spacer></v-spacer>
              <v-btn
                id="confirm-unschedule-course-btn"
                color="blue"
                text
                @click="unscheduleCourse()"
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
  import Context from '@/mixins/Context'
  import OxfordJoin from '@/components/util/OxfordJoin'
  import {unschedule} from '@/api/course'
  import {queueEmail} from '@/api/email'

  export default {
    name: 'CoursePageSidebar',
    components: {OxfordJoin},
    mixins: [Context],
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
      showUnscheduleModal: false
    }),
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
          this.afterUnschedule(data)
        }).catch(this.$ready)
      }
    }
  }
</script>