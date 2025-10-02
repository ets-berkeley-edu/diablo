<template>
  <v-card
    aria-labelledby="course-summary-header"
    class="pb-8 pt-6 px-6 px-md-4 px-lg-6 mx-1"
    role="region"
  >
    <h2 id="course-summary-header" class="sr-only">
      Course summary
    </h2>
    <v-row
      v-if="course.instructors.length"
      id="instructors"
      :class="{'line-through': course.deletedAt}"
    >
      <v-col cols="auto">
        <h3 class="sr-only">Instructors</h3>
        <v-icon color="primary" :icon="mdiSchoolOutline" />
      </v-col>
      <v-col>
        <OxfordJoin v-slot="{ item }" :items="course.instructors">
          <router-link
            v-if="currentUser.isAdmin"
            :id="`instructor-sidebar-link-${item.uid}`"
            :to="`/user/${item.uid}`"
          >
            {{ item.name }}
          </router-link>
          <span v-else :id="`instructor-sidebar-${item.uid}`">
            {{ item.name }}
          </span>
        </OxfordJoin>
      </v-col>
    </v-row>
    <div v-for="(meeting, index) in displayMeetings" :key="index">
      <v-divider v-if="index > 0" class="my-5 mx-12" />
      <h3 class="sr-only">
        Meetings
        {{ displayMeetings.length > 1
          ? `(${index + 1} of ${displayMeetings.length})`
          : ''
        }}
      </h3>
      <v-row
        v-if="meeting.daysNames"
        :id="`meeting-days-${index}`"
        :class="{'line-through': course.deletedAt}"
      >
        <v-col class="pb-0" cols="auto">
          <v-icon color="primary" :icon="mdiCalendar" />
        </v-col>
        <v-col class="pb-0">
          <Days :names-of-days="meeting.daysNames" />
          <div>
            <Date :date="meeting.startDate" /> to <Date :date="meeting.endDate" />
            <div
              v-if="course.scheduled && meeting.recordingEndDate && meeting.endDate !== meeting.recordingEndDate"
              class="font-size-14 text-medium-emphasis"
            >
              <div v-if="course.termId === config.currentTermId">
                (Final recording
                <span v-if="DateTime.fromISO(meeting.recordingEndDate) < today">was on </span>
                <span v-else-if="DateTime.fromISO(meeting.recordingEndDate) > today">scheduled for </span>
                <span v-else>is today, </span>
                <span class="text-no-wrap">
                  <Date :date="meeting.recordingEndDate" />)
                </span>
              </div>
              <div v-else-if="course.termId < config.currentTermId">
                <span>(Final recording was on </span>
                <span class="text-no-wrap">
                  <Date :date="meeting.recordingEndDate" />)
                </span>
              </div>
            </div>
          </div>
        </v-col>
      </v-row>
      <v-row
        v-if="meeting.startTimeFormatted"
        :id="`meeting-times-${index}`"
        :class="{'line-through': course.deletedAt}"
      >
        <v-col cols="auto" class="py-1">
          <v-icon color="primary" :icon="mdiClockOutline" />
        </v-col>
        <v-col class="py-1">
          <span aria-hidden="true">
            {{ meeting.startTimeFormatted }} - {{ meeting.endTimeFormatted }}
          </span>
          <span class="sr-only">
            {{ meeting.startTimeFormatted }} to {{ meeting.endTimeFormatted }}
          </span>
        </v-col>
      </v-row>
      <v-row
        v-if="meeting.room"
        :id="`rooms-${index}`"
        :class="{'line-through': course.deletedAt}"
      >
        <v-col class="py-1" cols="auto">
          <v-icon color="primary" :icon="mdiMapMarker" />
        </v-col>
        <v-col v-if="currentUser.isAdmin" class="py-1">
          <router-link :to="`/room/${meeting.room.id}`">
            {{ meeting.room.location }}
          </router-link>
        </v-col>
        <v-col v-else class="py-1">
          {{ meeting.room.location }}
        </v-col>
      </v-row>
    </div>
    <v-row v-if="course && course.crossListings.length" id="cross-listings" class="mt-3">
      <v-col class="py-1" cols="auto">
        <v-icon color="primary" :icon="mdiFormatLineSpacing" />
      </v-col>
      <v-col class="py-1">
        <span>
          {{ pluralize('Cross-listing', course.crossListings.length, false) }}
        </span>
        <div
          v-for="cl in course.crossListings"
          :id="`cross-listing-${cl.sectionId}`"
          :key="cl.sectionId"
        >
          {{ cl.label }}
        </div>
      </v-col>
    </v-row>
    <v-expand-transition>
      <v-row v-if="currentUser.isAdmin && course.hasOptedIn" id="opted-out" class="mt-3">
        <v-col class="py-1" cols="auto">
          <v-icon color="primary" :icon="mdiMinusCircle" />
        </v-col>
        <v-col class="py-1">Opted in</v-col>
      </v-row>
    </v-expand-transition>
    <CourseNotes />
  </v-card>
</template>

<script lang="ts" setup>
import {onMounted, ref} from 'vue'
import {DateTime} from 'luxon'
import {
  mdiCalendar,
  mdiClockOutline,
  mdiFormatLineSpacing,
  mdiMapMarker,
  mdiMinusCircle,
  mdiSchoolOutline
} from '@mdi/js'
import {storeToRefs} from 'pinia'
import type {Meeting} from '@/lib/types'
import {getDisplayMeetings} from '@/lib/berkeley'
import {pluralize} from '@/lib/utils'
import {useContextStore} from '@/stores/context'
import {useCourseStore} from '@/stores/course'
import CourseNotes from '@/components/course/CourseNotes.vue'
import Date from '@/components/util/Date.vue'
import Days from '@/components/util/Days.vue'
import OxfordJoin from '@/components/util/OxfordJoin.vue'

const courseStore = useCourseStore()
const {config, currentUser} = useContextStore()
const {course} = storeToRefs(courseStore)
const displayMeetings = ref<Meeting[]>([])
const today = ref(DateTime.local().startOf('day'))

onMounted(() => {
  displayMeetings.value = getDisplayMeetings(course.value)
})
</script>
