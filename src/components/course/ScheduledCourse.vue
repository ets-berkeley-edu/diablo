<template>
  <v-row aria-labelledby="" role="region">
    <v-col class="pa-4 my-2">
      <h3>Recordings scheduled</h3>
      <v-card
        v-for="scheduled in course.scheduled"
        :key="scheduled.kalturaScheduleId"
        class="my-2"
      >
        <v-card-title>
          <a
            id="link-to-edit-kaltura-event"
            class="text-subtitle-1"
            :href="`${config.kalturaMediaSpaceUrl}/recscheduling/index/edit-event/eventid/${scheduled.kalturaScheduleId}`"
            target="_blank"
          >
            Kaltura series {{ scheduled.kalturaScheduleId }}
            <span class="sr-only">(opens in new window)</span>
            <v-icon class="pb-1" :icon="mdiOpenInNew" size="small" />
          </a>
        </v-card-title>
        <v-card-text>
          <v-row>
            <v-col cols="6">
              <div class="text-subtitle-1">Scheduled on</div>
              <Date class="text-body-2 text-medium-emphasis" :date="scheduled.createdAt" tag="div" />
            </v-col>
            <v-col cols="6">
              <div class="text-subtitle-1">Recording Type</div>
              <div class="text-body-2 text-medium-emphasis">{{ scheduled.recordingTypeName }}</div>
            </v-col>
          </v-row>
          <v-row>
            <v-col cols="6">
              <div class="text-subtitle-1">Publish Type</div>
              <div class="text-body-2 text-medium-emphasis">{{ scheduled.publishTypeName }}</div>
            </v-col>
            <v-col cols="6">
              <div class="text-subtitle-1">Collaborator UIDs</div>
              <div id="scheduled-collaborator-uids" class="text-body-2 text-medium-emphasis">
                {{ scheduled.collaboratorUids.length
                  ? scheduled.collaboratorUids.join(', ')
                  : 'None'
                }}
              </div>
            </v-col>
          </v-row>
        </v-card-text>
      </v-card>
    </v-col>
  </v-row>
</template>

<script setup>
import {mdiOpenInNew} from '@mdi/js'
import Date from '@/components/util/Date'
import {useContextStore} from '@/stores/context'

defineProps({
  course: {
    type: Object,
    required: true
  }
})

const {config} = useContextStore()
</script>
