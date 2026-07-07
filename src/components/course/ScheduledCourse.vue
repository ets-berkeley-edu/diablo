<template>
  <div aria-labelledby="recordings-scheduled-header" class="px-4" role="region">
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
  </div>
</template>

<script lang="ts" setup>
import {isEmpty} from 'lodash'
import {useContextStore} from '@/stores/context'
import {useCourseStore} from '@/stores/course'
import Date from '@/components/util/Date.vue'
import ExternalLink from '@/components/util/ExternalLink.vue'

const {config} = useContextStore()
const {course} = useCourseStore()
</script>
