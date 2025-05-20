<template>
  <div
    aria-labelledby="course-summary-header"
    class="elevation-2 pa-6"
    role="region"
  >
    <h2 id="course-summary-header" class="sr-only">
      Course summary: {{ course.label }}
    </h2>

    <v-row
      v-if="instructors.length"
      id="instructors"
      :class="{ 'line-through': course.deletedAt }"
    >
      <v-col cols="auto">
        <h3 class="sr-only">Instructors</h3>
        <v-icon aria-label="Mortarboard icon">mdi-school-outline</v-icon>
      </v-col>
      <v-col>
        <OxfordJoin v-slot="{ item }" :items="instructors">
          <router-link
            v-if="currentUser.isAdmin"
            :id="`instructor-sidebar-link-${item.uid}`"
            aria-label="Link to instructor page"
            :to="`/user/${item.uid}`"
          >
            {{ item.name }}
          </router-link>
          <span
            v-else
            :id="`instructor-sidebar-${item.uid}`"
          >{{ item.name }}</span>
        </OxfordJoin>

        <div
          v-if="instructorProxies.length"
          class="text--secondary subtitle-2"
        >
          (
          <OxfordJoin v-slot="{ item }" :items="instructorProxies">
            <span :id="`instructor-proxy-${item.uid}`">{{ item.name }}</span>
          </OxfordJoin>
          {{ instructorProxies.length === 1
            ? 'is an Admin Proxy'
            : 'are Admin Proxies'
          }}.)
        </div>
      </v-col>
    </v-row>

    <!-- Meetings -->
    <div
      v-for="(meeting, index) in displayMeetings"
      :key="index"
    >
      <h3 class="sr-only">
        Meeting
        {{ displayMeetings.length > 1
          ? `#${index + 1} of ${displayMeetings.length}`
          : ''
        }}
      </h3>

      <!-- Days & Dates -->
      <v-row
        v-if="meeting.daysNames"
        :id="`meeting-days-${index}`"
        :class="{ 'line-through': course.deletedAt }"
      >
        <v-col
          cols="auto"
          :class="{ 'pb-0': displayMeetings.length > 1 }"
        >
          <v-icon aria-label="Calendar icon">mdi-calendar</v-icon>
        </v-col>
        <v-col :class="{ 'pb-0': displayMeetings.length > 1 }">
          <Days :names-of-days="meeting.daysNames" />
          <div>
            <span class="sr-only">Dates:</span>
            {{ DateTime.fromISO(meeting.startDate).toFormat('MMM d, yyyy') }}
            to
            {{ DateTime.fromISO(meeting.endDate).toFormat('MMM d, yyyy') }}

            <div
              v-if="course.scheduled && !course.hasOptedOut && meeting.recordingEndDate && meeting.endDate !== meeting.recordingEndDate"
              class="font-weight-light"
            >
              <div v-if="course.termId === config.currentTermId">
                (Final recording
                <span v-if="DateTime.fromISO(meeting.recordingEndDate) < today">was on</span>
                <span
                  v-else-if="
                    DateTime.fromISO(meeting.recordingEndDate) > today
                  "
                >scheduled for</span>
                <span
                  v-else
                >is today, </span>
                {{ DateTime.fromISO(meeting.recordingEndDate).toFormat('MMM d, yyyy') }}.)
              </div>
              <div v-else-if="course.termId < config.currentTermId">
                (Final recording was on
                {{ DateTime.fromISO(meeting.recordingEndDate).toFormat('MMM d, yyyy') }}
                .)
              </div>
            </div>
          </div>
        </v-col>
      </v-row>

      <!-- Times -->
      <v-row
        v-if="meeting.startTimeFormatted"
        :id="`meeting-times-${index}`"
        :class="{ 'line-through': course.deletedAt }"
      >
        <v-col
          cols="auto"
          :class="{ 'pb-1 pt-1': displayMeetings.length > 1 }"
        >
          <v-icon aria-label="Clock icon">mdi-clock-outline</v-icon>
        </v-col>
        <v-col :class="{ 'pb-1 pt-1': displayMeetings.length > 1 }">
          <span class="sr-only">Start and end times:</span>
          <span aria-hidden="true">
            {{ meeting.startTimeFormatted }} -
            {{ meeting.endTimeFormatted }}
          </span>
          <span class="sr-only">
            {{ meeting.startTimeFormatted }} to
            {{ meeting.endTimeFormatted }}
          </span>
        </v-col>
      </v-row>

      <!-- Room -->
      <v-row
        v-if="meeting.room"
        :id="`rooms-${index}`"
        :class="{ 'line-through': course.deletedAt }"
      >
        <v-col
          cols="auto"
          :class="{ 'pb-5 pt-1': displayMeetings.length > 1 }"
        >
          <v-icon aria-label="Map icon">mdi-map-marker</v-icon>
        </v-col>
        <v-col
          v-if="currentUser.isAdmin"
          :class="{ 'pb-5 pt-1': displayMeetings.length > 1 }"
        >
          <router-link
            :to="`/room/${meeting.room.id}`"
            aria-label="Link to room page"
          >
            {{ meeting.room.location }}
          </router-link>
        </v-col>
        <v-col v-else>
          <span class="sr-only">Location:</span>
          {{ meeting.room.location }}
        </v-col>
      </v-row>
    </div>

    <!-- Cross-Listings -->
    <v-row
      v-if="course.crossListings.length"
      id="cross-listings"
    >
      <v-col cols="auto">
        <v-icon aria-label="List icon">mdi-format-line-spacing</v-icon>
      </v-col>
      <v-col>
        <span>
          Cross-listing<span v-if="course.crossListings.length !== 1">s</span>
        </span>
        <div
          v-for="cl in course.crossListings"
          :key="cl.sectionId"
          :id="`cross-listing-${cl.sectionId}`"
        >
          {{ cl.label }}
        </div>
      </v-col>
    </v-row>

    <!-- Opt-Out Flag -->
    <v-row
      v-if="currentUser.isAdmin && course.hasOptedOut"
      id="opted-out"
    >
      <v-col cols="auto">
        <v-icon aria-label="'Do not disturb' icon">mdi-minus-circle</v-icon>
      </v-col>
      <v-col>Opted out</v-col>
    </v-row>
  </div>
</template>

<script setup>
import {defineProps, ref, onMounted} from 'vue'
import {DateTime} from 'luxon'
import {filter} from 'lodash'
import {useContextStore} from '@/stores/context'
import Days from '@/components/util/Days'
import OxfordJoin from '@/components/util/OxfordJoin'
import Utils from '@/mixins/Utils'

// props
const props = defineProps({
  course: {
    type: Object,
    required: true
  }
})

// Pinia store for config & user
const {config, currentUser} = useContextStore()

// reactive state
const displayMeetings = ref([])
const instructors = ref([])
const instructorProxies = ref([])
const today = ref(DateTime.local().startOf('day'))

// utility
const {getDisplayMeetings} = Utils.methods

onMounted(() => {
  displayMeetings.value = getDisplayMeetings(props.course)
  instructors.value = filter(props.course.instructors, i => i.roleCode !== 'APRX')
  instructorProxies.value = filter(props.course.instructors, i => i.roleCode === 'APRX')
})
</script>
