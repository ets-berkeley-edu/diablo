<template>
  <v-card
    aria-labelledby="course-summary-header"
    class="pb-8 pt-6 px-6 px-md-4 px-lg-6 mx-1"
    role="region"
  >
    <v-card-text class="font-size-16 pa-1">
      <h2 id="course-summary-header" class="sr-only">
        Course summary
      </h2>
      <dl>
        <template v-if="course.instructors.length">
          <div class="align-start d-flex">
            <dt class="mr-4">
              <span class="sr-only">Instructors</span>
              <v-icon color="primary" :icon="mdiSchoolOutline" />
            </dt>
            <dd>
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
            </dd>
          </div>
        </template>
        <template v-if="displayMeetings.length">
          <div
            v-for="(meeting, index) in displayMeetings"
            :key="index"
          >
            <v-divider v-if="displayMeetings.length > 1" class="my-4 mx-10" />
            <div class="align-start d-flex mt-4">
              <dt class="mr-4">
                <v-icon color="primary" :icon="mdiCalendar" />
                <span class="sr-only">Meetings {{ displayMeetings.length > 1 ? `(${index + 1} of ${displayMeetings.length})` : '' }}</span>
              </dt>
              <dd>
                <div
                  v-if="meeting.daysNames"
                  :id="`meeting-days-${index}`"
                  :class="{'line-through': course.deletedAt}"
                >
                  <Days :names-of-days="meeting.daysNames" />
                  <div class="mt-1">
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
                </div>
              </dd>
            </div>
            <div
              v-if="meeting.startTimeFormatted"
              :id="`meeting-times-${index}`"
              class="align-center d-flex mt-2"
            >
              <dt class="mr-4">
                <v-icon color="primary" :icon="mdiClockOutline" />
              </dt>
              <dd>
                <span aria-hidden="true" class="text-no-wrap">
                  {{ meeting.startTimeFormatted }} - {{ meeting.endTimeFormatted }}
                </span>
                <span class="sr-only">
                  {{ meeting.startTimeFormatted }} to {{ meeting.endTimeFormatted }}
                </span>
              </dd>
            </div>
            <div
              v-if="meeting.room"
              :id="`rooms-${index}`"
              :class="{'line-through': course.deletedAt}"
              class="align-center d-flex mt-4"
            >
              <dt class="mr-4">
                <v-icon color="primary" :icon="mdiMapMarker" />
              </dt>
              <dd class="text-no-wrap">
                <router-link v-if="currentUser.isAdmin" :to="`/room/${meeting.room.id}`">
                  {{ meeting.room.location }}
                </router-link>
                <div v-if="!currentUser.isAdmin">
                  {{ meeting.room.location }}
                </div>
              </dd>
            </div>
            <v-divider v-if="displayMeetings.length > 1 && index === displayMeetings.length - 1" class="my-4 mx-10" />
          </div>
        </template>
        <template v-if="course && course.crossListings.length">
          <div id="cross-listings" class="align-start d-flex mt-4">
            <dt class="mr-4">
              <v-icon color="primary" :icon="mdiFormatLineSpacing" />
            </dt>
            <dd>
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
            </dd>
          </div>
        </template>
        <v-expand-transition v-if="currentUser.isAdmin">
          <div v-if="course.hasOptedIn" id="opted-out" class="align-center d-flex mt-4">
            <dt class="mr-4">
              <v-icon color="primary" :icon="mdiCheckboxMarkedCircle" />
            </dt>
            <dd class="text-no-wrap">Opted in</dd>
          </div>
        </v-expand-transition>
      </dl>
    </v-card-text>
    <v-card-actions>
      <CourseNotes class="mt-4 w-100" />
    </v-card-actions>
  </v-card>
</template>

<script lang="ts" setup>
import {onMounted, ref} from 'vue'
import {DateTime} from 'luxon'
import {
  mdiCalendar,
  mdiCheckboxMarkedCircle,
  mdiClockOutline,
  mdiFormatLineSpacing,
  mdiMapMarker,
  mdiSchoolOutline,
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

const {config, currentUser} = useContextStore()
const {course} = storeToRefs(useCourseStore())
const displayMeetings = ref<Meeting[]>([])
const today = ref(DateTime.local().startOf('day'))

onMounted(() => {
  displayMeetings.value = getDisplayMeetings(course.value)
})
</script>
