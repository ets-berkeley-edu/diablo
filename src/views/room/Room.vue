<template>
  <div v-if="!contextStore.loading">
    <v-card class="border-sm">
      <v-card-title class="pb-0">
        <PageTitle :icon="mdiHomeCityOutline" :text="room.location" />
      </v-card-title>
      <v-card-text>
        <v-container class="d-block font-size-16 mx-0 mb-6" fluid>
          <v-row v-if="room.kalturaResourceId">
            <v-col class="text-subtitle-1">
              Kaltura resource ID: {{ room.kalturaResourceId }}
              <span v-if="kalturaEventList">
                (<a
                  id="skip-to-kaltura-event-list"
                  href="#kaltura-events-header"
                  @click.stop="scrollToKalturaEvents"
                >
                  Scroll to Kaltura events
                </a>)
              </span>
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
            <v-col class="d-flex justify-end pr-4" cols="12" sm="5">
              <v-switch
                v-model="isAuditorium"
                :aria-describedby="undefined"
                color="primary"
                hide-details
                label="Auditorium"
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
                <v-icon color="anchor" :icon="mdiPrinter" /> Print schedule <span class="sr-only">(opens in new tab)</span>
              </router-link>
            </v-col>
          </v-row>
        </v-container>
        <CoursesDataTable
          :courses="room.courses"
          :include-room-column="false"
          :message-for-courses="summarize(room.courses)"
          :refreshing="false"
        />
      </v-card-text>
    </v-card>
    <v-card v-if="kalturaEventList" class="mt-8 border-sm">
      <v-card-title>
        <h2 id="kaltura-events-header" tabindex="-1">The Kaltura Events of {{ room.location }}</h2>
        <div class="text-subtitle-2">
          Kaltura events tagged with '{{ contextStore.config.createdByDiabloTag }}' and
          a start-date between {{ contextStore.config.currentTermRecordingsBegin }} and  {{ contextStore.config.currentTermRecordingsEnd }}.
        </div>
      </v-card-title>
      <v-card-text class="pt-5">
        <KalturaEventList :events="kalturaEventList" :location="room.location" />
      </v-card-text>
    </v-card>
  </div>
</template>

<script setup>
import {each, find, get} from 'lodash'
import {mdiHomeCityOutline, mdiPrinter} from '@mdi/js'
import {onMounted, ref, watch} from 'vue'
import {useGoTo} from 'vuetify'
import {useRoute} from 'vue-router'
import CoursesDataTable from '@/components/course/CoursesDataTable'
import KalturaEventList from '@/components/kaltura/KalturaEventList'
import PageTitle from '@/components/util/PageTitle'
import SelectRoomCapability from '@/components/room/SelectRoomCapability'
import {alertScreenReader, getCourseCodes, putFocusNextTick, summarize} from '@/lib/utils'
import {getKalturaEventList, getRoom, setAuditorium} from '@/api/room'
import {useContextStore} from '@/stores/context'

const contextStore = useContextStore()
const isAuditorium = ref(undefined)
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

const scrollToKalturaEvents = () => {
  putFocusNextTick('kaltura-events-header', {scroll: false})
  goTo('#kaltura-events-header', {duration: 300, offset: -70, easing: 'easeInOutCubic'})
}
</script>

