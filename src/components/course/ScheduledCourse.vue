<template>
  <div>
    <h4 class="title">Recordings scheduled</h4>

    <!-- one v-list per scheduled entry -->
    <v-list
      v-for="scheduled in course.scheduled"
      :key="scheduled.kalturaScheduleId"
    >
      <!-- Edit link for admins -->
      <v-list-item-title class="pl-4 pt-3">
        <div v-if="currentUser.isAdmin" class="d-flex align-bottom">
          <a
            id="link-to-edit-kaltura-event"
            aria-label="Open Kaltura MediaSpace in a new window"
            class="text-anchor"
            :href="`${config.kalturaMediaSpaceUrl}/recscheduling/index/edit-event/eventid/${scheduled.kalturaScheduleId}`"
            target="_blank"
          >
            Kaltura series {{ scheduled.kalturaScheduleId }}
            <v-icon small class="pb-1">mdi-open-in-new</v-icon>
          </a>
        </div>
      </v-list-item-title>

      <!-- “Scheduled on” & “Recording Type” side by side -->
      <v-list-item two-line>
        <v-list-item-title>Scheduled on</v-list-item-title>
        <v-list-item-subtitle>{{ formatDate(scheduled.createdAt) }}</v-list-item-subtitle>

        <v-list-item-title>Recording Type</v-list-item-title>
        <v-list-item-subtitle>{{ scheduled.recordingTypeName }}</v-list-item-subtitle>
      </v-list-item>

      <!-- “Publish Type” & “Collaborator UIDs” side by side -->
      <v-list-item two-line>
        <v-list-item-title>Publish Type</v-list-item-title>
        <v-list-item-subtitle>{{ scheduled.publishTypeName }}</v-list-item-subtitle>

        <v-list-item-title>Collaborator UIDs</v-list-item-title>
        <v-list-item-subtitle id="scheduled-collaborator-uids">
          {{ scheduled.collaboratorUids.length
            ? scheduled.collaboratorUids.join(', ')
            : 'None'
          }}
        </v-list-item-subtitle>
      </v-list-item>
    </v-list>
  </div>
</template>

<script setup>
import {defineProps} from 'vue'
import {DateTime} from 'luxon'
import {useContextStore} from '@/stores/context'

// declare props
defineProps({
  course: {
    type: Object,
    required: true
  }
})

const {config, currentUser} = useContextStore()

function formatDate(iso) {
  return DateTime.fromISO(iso).toFormat('MMM dd, yyyy')
}
</script>
