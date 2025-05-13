<template>
  <div v-if="!contextStore.loading">
    <v-card class="border-sm">
      <v-card-title class="pb-0">
        <PageTitle :icon="mdiHomeCityOutline" :text="room.location" />
      </v-card-title>
      <v-card-actions>
        <v-list class="w-100" dense>
          <v-list-item v-if="room.kalturaResourceId">
            <div class="subtitle-1">
              Kaltura resource ID: {{ room.kalturaResourceId }}
              <span v-if="kalturaEventList">
                (<a id="skip-to-kaltura-event-list" href="#kaltura-events-header" @click="scrollToKalturaEvents">Scroll to Kaltura events</a>)
              </span>
            </div>
          </v-list-item>
          <v-list-item>
            <div class="align-end d-flex w-100">
              <div class="pb-4 pr-3">
                <label for="select-room-capability" class="subtitle-1">Capability:</label>
              </div>
              <div>
                <SelectRoomCapability
                  :on-update="onUpdateRoomCapability"
                  :options="contextStore.config.roomCapabilityOptions"
                  :room="room"
                />
              </div>
              <div class="ml-auto">
                <v-switch v-model="isAuditorium" label="Auditorium"></v-switch>
              </div>
            </div>
          </v-list-item>
          <v-list-item v-if="offerPrintable">
            <router-link
              :id="`print-room-${room.id}-schedule`"
              aria-label="Open printable version of this page, in a new window"
              class="subtitle-1"
              target="_blank"
              :to="`/room/printable/${room.id}`"
            >
              <v-icon class="linked-icon" :icon="mdiPrinter" /> Print schedule<span class="sr-only"> (opens a new browser tab)</span>
            </router-link>
          </v-list-item>
        </v-list>
      </v-card-actions>
      <v-card-text>
        <CoursesDataTable
          :courses="room.courses"
          :include-room-column="false"
          :message-for-courses="summarize(room.courses)"
          :refreshing="false"
        />
      </v-card-text>
    </v-card>
    <div v-if="kalturaEventList" class="ma-3 pt-5">
      <h2 id="kaltura-events-header" tabindex="-1">The Kaltura Events of {{ room.location }}</h2>
      <div class="subtitle-2">
        Kaltura events tagged with '{{ contextStore.config.createdByDiabloTag }}' and
        a start-date between {{ contextStore.config.currentTermRecordingsBegin }} and  {{ contextStore.config.currentTermRecordingsEnd }}.
      </div>
      <KalturaEventList :events="kalturaEventList" :location="room.location" />
    </div>
  </div>
</template>

<script setup>
import {each, find, get} from 'lodash'
import {mdiHomeCityOutline, mdiPrinter} from '@mdi/js'
import {onMounted, ref, watch} from 'vue'
import {useRoute} from 'vue-router'
import CoursesDataTable from '@/components/course/CoursesDataTable'
import KalturaEventList from '@/components/kaltura/KalturaEventList'
import PageTitle from '@/components/util/PageTitle'
import SelectRoomCapability from '@/components/room/SelectRoomCapability'
import {alertScreenReader, getCourseCodes, summarize} from '@/lib/utils'
import {getKalturaEventList, getRoom, setAuditorium} from '@/api/room'
import {useContextStore} from '@/stores/context'

const contextStore = useContextStore()
const isAuditorium = ref(undefined)
const kalturaEventList = ref([])
const offerPrintable = ref(undefined)
const room = ref(undefined)
const route = useRoute()

contextStore.loadingStart()

onMounted(() => {
  let roomId = get(route, 'params.id')
  getRoom(roomId).then(data => {
    room.value = data
    isAuditorium.value = data.isAuditorium
    each(room.value.courses, course => {
      course.courseCodes = getCourseCodes(course)
    })
    offerPrintable.value = !!find(room.value.courses, c => find(c.scheduled, s => s.room.id === room.value.id))
    contextStore.loadingComplete(data.location)
    // The page is ready; Kaltura events will pop up in a sec.
    if (room.value.kalturaResourceId) {
      getKalturaEventList(room.value.kalturaResourceId).then(data => {
        kalturaEventList.value = data
      })
    }
  })
})

watch(isAuditorium, value => {
  if (!contextStore.loading) {
    setAuditorium(room.value.id, value).then(() => {
      room.value.isAuditorium = value
    })
  }
})

const onUpdateRoomCapability = capability => {
  room.value.capability = capability
  alertScreenReader(capability ? `'${capability}' selected` : 'Room capability removed.')
}
</script>
