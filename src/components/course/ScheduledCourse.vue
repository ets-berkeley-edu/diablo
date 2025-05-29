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
            :href="`${config.kalturaMediaSpaceUrl}/recscheduling/index/edit-event/eventid/${scheduled.kalturaScheduleId}`"
            target="_blank"
          >
            Kaltura series {{ scheduled.kalturaScheduleId }}
            <v-icon small class="pb-1" :icon="mdiOpenInNew"></v-icon>
          </a>
        </div>
      </v-list-item-title>

      <!-- “Scheduled on” & “Recording Type” side by side -->
      <v-list-item>
        <v-row class="w-100 mb-1 mt-1">
          <v-col cols="6">
            <div class="text-subtitle-1">Scheduled on</div>
            <div class="text-body-2">{{ formatDate(scheduled.createdAt) }}</div>
          </v-col>
          <v-col cols="6">
            <div class="text-subtitle-1">Recording Type</div>
            <div class="text-body-2">{{ scheduled.recordingTypeName }}</div>
          </v-col>
        </v-row>
      </v-list-item>

      <!-- “Publish Type” & “Collaborator UIDs” side by side -->
      <v-list-item>
        <v-row class="w-100">
          <v-col cols="6">
            <div class="text-subtitle-1">Publish Type</div>
            <div class="text-body-2">{{ scheduled.publishTypeName }}</div>
          </v-col>
          <v-col cols="6">
            <div class="text-subtitle-1">Collaborator UIDs</div>
            <div class="text-body-2" id="scheduled-collaborator-uids">
              {{ scheduled.collaboratorUids.length
                ? scheduled.collaboratorUids.join(', ')
                : 'None'
              }}
            </div>
          </v-col>
        </v-row>
      </v-list-item>
    </v-list>
  </div>
</template>

<script setup>
import {DateTime} from 'luxon'
import {useContextStore} from '@/stores/context'
import {mdiOpenInNew} from '@mdi/js'

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
