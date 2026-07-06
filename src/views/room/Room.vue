<template>
  <div v-if="!contextStore.loading">
    <v-card elevation="0">
      <v-card-title class="py-0">
        <PageTitle :icon="mdiHomeCityOutline" :text="room.location" />
      </v-card-title>
      <v-card-text>
        <v-container class="d-block font-size-16 mx-0 mb-6 pa-0" fluid>
          <v-row v-if="room.kalturaResourceId">
            <v-col class="text-subtitle-1">
              <a
                v-if="kalturaEventList"
                id="skip-to-kaltura-event-list"
                class="font-size-18 text-no-wrap"
                href="#kaltura-events-header"
                @click.stop="scrollToKalturaEvents"
              >
                Scroll to Kaltura events
              </a>
            </v-col>
            <v-col class="text-no-wrap text-right">
              <span class="font-weight-bold">Kaltura resource ID:</span> {{ room.kalturaResourceId }}
            </v-col>
          </v-row>
          <v-row>
            <v-col cols="12" sm="7">
              <SelectRoomCapability
                :on-update="onUpdateRoomCapability"
                :options="contextStore.config.roomCapabilityOptions"
                :room="room"
              />
            </v-col>
          </v-row>
          <v-row v-if="offerPrintable">
            <v-col>
              <router-link
                :id="`print-room-${room.id}-schedule`"
                class="text-subtitle-1"
                target="_blank"
                :to="`/room/printable/${room.id}`"
              >
                <v-icon class="mr-2" color="anchor" :icon="mdiPrinter" />
                Print schedule<span class="sr-only">&nbsp;(opens in new tab)</span>
              </router-link>
            </v-col>
          </v-row>
        </v-container>
        <CoursesDataTable
          :courses="room.courses"
          :include-room-column="false"
          :message-for-courses="summarize(room.courses)"
          :refreshing="false"
          :show-opt-in="false"
        />
      </v-card-text>
    </v-card>
    <v-card v-if="kalturaEventList" class="mt-8 pa-4 border-sm">
      <v-card-title>
        <h2 id="kaltura-events-header" tabindex="-1">The Kaltura Events of {{ room.location }}</h2>
        <div class="text-subtitle-2 text-wrap">
          Kaltura events tagged with '{{ contextStore.config.createdByDiabloTag }}' and
          a start-date between {{ contextStore.config.currentTermRecordingsBegin }} and  {{ contextStore.config.currentTermRecordingsEnd }}.
        </div>
      </v-card-title>
      <v-card-text>
        <KalturaEventList
          :events="kalturaEventList"
          :is-loading="isLoadingEventList"
          :location="room.location"
        />
      </v-card-text>
    </v-card>
  </div>
</template>

<script setup>
import {each, find, get} from 'lodash'
import {mdiHomeCityOutline, mdiPrinter} from '@mdi/js'
import {onMounted, ref} from 'vue'
import {useGoTo} from 'vuetify'
import {useRoute} from 'vue-router'
import CoursesDataTable from '@/components/course/CoursesDataTable'
import KalturaEventList from '@/components/kaltura/KalturaEventList'
import PageTitle from '@/components/util/PageTitle'
import SelectRoomCapability from '@/components/room/SelectRoomCapability'
import {getCourseCodes} from '@/lib/berkeley'
import {putFocusNextTick, summarize} from '@/lib/utils'
import {getKalturaEventList, getRoom} from '@/api/room'
import {useContextStore} from '@/stores/context'

const contextStore = useContextStore()
const isLoadingEventList = ref(true)
const kalturaEventList = ref([])
const offerPrintable = ref(undefined)
const room = ref(undefined)
const route = useRoute()
const goTo = useGoTo()

contextStore.loadingStart()

onMounted(() => {
  const roomId = get(route, 'params.id')
  getRoom(roomId).then(data => {
    room.value = data
    each(room.value.courses, course => {
      course.courseCodes = getCourseCodes(course)
    })
    offerPrintable.value = !!find(room.value.courses, c => find(c.scheduled, s => s.room.id === room.value.id))
    contextStore.loadingComplete(data.location)

    // The page is ready; Kaltura events will pop up in a sec.
    if (room.value.kalturaResourceId) {
      getKalturaEventList(room.value.kalturaResourceId).then(data => {
        kalturaEventList.value = data
        isLoadingEventList.value = false
      })
    }
  })
})

const onUpdateRoomCapability = capability => {
  room.value.capability = capability
}

const scrollToKalturaEvents = () => {
  putFocusNextTick('kaltura-events-header', {scroll: false})
  goTo('#kaltura-events-header', {duration: 300, offset: -70, easing: 'easeInOutCubic'})
}
</script>

