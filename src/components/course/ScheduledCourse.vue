<template>
  <v-row aria-labelledby="recordings-scheduled-header" role="region">
    <v-col class="pa-4 my-2">
      <h3 id="recordings-scheduled-header">Recordings scheduled</h3>
      <div v-if="isEmpty(course.scheduled)" id="recordings-scheduled-none" class="pl-4 pt-2 text-medium-emphasis">
        No scheduled recordings
      </div>
      <v-card
        v-for="scheduled in course.scheduled"
        :key="scheduled.kalturaScheduleId"
        variant="text"
        class="my-2"
      >
        <v-card-title>
          <ExternalLink
            class="text-subtitle-1"
            :href="`${config.kalturaMediaSpaceUrl}/recscheduling/index/edit-event/eventid/${scheduled.kalturaScheduleId}`"
            :icon-size="16"
            link-id="link-to-edit-kaltura-event"
            :text="`Kaltura series ${scheduled.kalturaScheduleId}`"
          />
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

<script lang="ts" setup>
import type {PropType} from 'vue'
import {isEmpty} from 'lodash'
import type {Course} from '@/lib/types'
import {useContextStore} from '@/stores/context'
import Date from '@/components/util/Date.vue'
import ExternalLink from '@/components/util/ExternalLink.vue'

defineProps({
  course: {
    type: Object as PropType<Course>,
    required: true
  }
})

const {config} = useContextStore()
</script>
