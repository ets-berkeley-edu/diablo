<template>
  <div>
    <h4 class="title">Recordings scheduled</h4>
    <v-list v-for="scheduled in course.scheduled" :key="scheduled.kalturaScheduleId">
      <v-list-item-title class="pl-4 pt-3">
        <div v-if="$currentUser.isAdmin" class="d-flex align-bottom">
          <div>
            <a
              id="link-to-edit-kaltura-event"
              :href="`${$config.kalturaMediaSpaceUrl}/recscheduling/index/edit-event/eventid/${scheduled.kalturaScheduleId}`"
              target="_blank"
              aria-label="Open Kaltura MediaSpace in a new window"
            >
              Kaltura series {{ scheduled.kalturaScheduleId }} <v-icon small class="pb-1">mdi-open-in-new</v-icon>
            </a>
          </div>
        </div>
      </v-list-item-title>
      <v-list-item two-line>
        <v-list-item-content>
          <v-list-item-title>Scheduled on</v-list-item-title>
          <v-list-item-subtitle>{{ scheduled.createdAt | moment('MMM DD, YYYY') }}</v-list-item-subtitle>
        </v-list-item-content>
        <v-list-item-content>
          <v-list-item-title>Recording Type</v-list-item-title>
          <v-list-item-subtitle>{{ scheduled.recordingTypeName }}</v-list-item-subtitle>
        </v-list-item-content>
      </v-list-item>
      <v-list-item two-line>
        <v-list-item-content>
          <v-list-item-title>Publish Type</v-list-item-title>
          <v-list-item-subtitle>{{ scheduled.publishTypeName }}</v-list-item-subtitle>
        </v-list-item-content>
        <v-list-item-content>
          <v-list-item-title>Collaborator UIDs</v-list-item-title>
          <v-list-item-subtitle id="scheduled-collaborator-uids">
            {{ scheduled.collaboratorUids.length ? scheduled.collaboratorUids : 'None' }}
          </v-list-item-subtitle>
        </v-list-item-content>
      </v-list-item>
    </v-list>
  </div>
</template>

<script>
import Context from '@/mixins/Context'
import Utils from '@/mixins/Utils'

export default {
  name: 'ScheduledCourse',
  mixins: [Context, Utils],
  props: {
    course: {
      required: true,
      type: Object
    }
  },
  data: () => ({
    agreedToTerms: false,
  })
}
</script>
