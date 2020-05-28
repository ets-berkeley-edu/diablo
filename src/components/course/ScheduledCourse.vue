<template>
  <v-card tile>
    <v-list-item-title class="pl-4 pt-4">
      <h4 class="title">Recordings scheduled</h4>
      <div v-if="$currentUser.isAdmin" class="d-flex align-bottom">
        <v-dialog v-if="$currentUser.isAdmin && course.scheduled.kalturaSchedule" v-model="kalturaScheduleDialogJSON">
          <template v-slot:activator="{ on }">
            <v-btn
              class="pa-0"
              text
              x-small
              v-on="on"
            >
              <v-icon id="kaltura-schedule-dialog" class="pb-2" v-on="on">
                mdi-code-json
              </v-icon>
            </v-btn>
          </template>
          <v-card>
            <v-card-title primary-title>
              Raw JSON of Kaltura schedule
            </v-card-title>
            <v-card-text>
              <pre>{{ course.scheduled.kalturaSchedule }}</pre>
            </v-card-text>
            <v-divider></v-divider>
            <v-card-actions>
              <v-spacer></v-spacer>
              <v-btn
                color="primary"
                text
                @click="kalturaScheduleDialogJSON = false"
              >
                Close
              </v-btn>
            </v-card-actions>
          </v-card>
        </v-dialog>
        <div>
          <a
            id="link-to-edit-kaltura-event"
            :href="`${$config.kalturaMediaSpaceUrl}/recscheduling/index/edit-event/eventid/${course.scheduled.kalturaScheduleId}`"
            target="_blank"
            aria-label="Open Kaltura MediaSpace in a new window"
          >
            Kaltura event {{ course.scheduled.kalturaScheduleId }} <v-icon small class="pb-1">mdi-open-in-new</v-icon>
          </a>
        </div>
      </div>
    </v-list-item-title>
    <v-list-item two-line class="pb-3">
      <v-list-item-content>
        <v-list-item-title>Scheduled on</v-list-item-title>
        <v-list-item-subtitle>{{ course.scheduled.createdAt | moment('MMM DD, YYYY') }}</v-list-item-subtitle>
      </v-list-item-content>
      <v-list-item-content>
        <v-list-item-title>Recording Type</v-list-item-title>
        <v-list-item-subtitle>{{ course.scheduled.recordingTypeName }}</v-list-item-subtitle>
      </v-list-item-content>
      <v-list-item-content>
        <v-list-item-title>Publish Type</v-list-item-title>
        <v-list-item-subtitle>{{ course.scheduled.publishTypeName }}</v-list-item-subtitle>
      </v-list-item-content>
    </v-list-item>
    <v-card-text>
      <CourseCaptureExplained />
    </v-card-text>
  </v-card>
</template>

<script>
  import CourseCaptureExplained from '@/components/util/CourseCaptureExplained'

  export default {
    name: 'ScheduledCourse',
    components: {CourseCaptureExplained},
    props: {
      course: {
        required: true,
        type: Object
      }
    },
    data: () => ({
      kalturaScheduleDialogJSON: false
    })
  }
</script>
