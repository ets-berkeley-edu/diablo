<template>
  <v-card v-if="!contextStore.loading" outlined class="elevation-1">
    <v-card-title class="align-start">
      <div class="pt-2">
        <PageTitle :icon="mdiAutoFix" text="The Ouija Board" />
        <v-btn
          v-if="courses.length"
          class="ml-8"
          :disabled="isDownloading || isRefreshing"
          text
          @click="onClickDownload"
        >
          <v-progress-circular
            v-if="isDownloading"
            class="mr-2"
            color="primary"
            indeterminate
            size="18"
            width="3"
          ></v-progress-circular>
          {{ isDownloading ? 'Downloading' : 'Download CSV' }}
        </v-btn>
      </div>
      <v-spacer></v-spacer>
      <div class="float-right w-50">
        <v-text-field
          id="input-search"
          v-model="searchText"
          :append-icon="mdiMagnify"
          aria-label="Search courses table"
          clearable
          :disabled="isDownloading"
          label="Search"
          single-line
          hide-details
        ></v-text-field>
        <div class="d-flex">
          <v-select
            id="ouija-filter-options"
            :model="selectedFilter"
            aria-label="Filter courses table"
            color="secondary"
            :disabled="isDownloading"
            :items="keys(contextStore.config.searchFilterOptions)"
            @update:model-value="() => refresh(`Courses table refreshed. Showing ${contextStore.config.searchFilterOptions[selectedFilter]}`)"
          >
            <span :id="`filter-option-${data.item.value}`" slot="item" slot-scope="data">{{ data.item }}</span>
            <template #selection="{item}">
              <v-tooltip id="tooltip-ouija-filter" bottom>
                <template #activator="{props}">
                  <v-btn
                    class="pb-1 pr-2"
                    icon
                    v-bind="props"
                  >
                    <v-icon :icon="mdiInformationOutline" />
                  </v-btn>
                </template>
                <span class="font-weight-bold">{{ selectedFilter }}:</span> {{ contextStore.config.searchFilterOptions[selectedFilter] }}
              </v-tooltip>
              {{ item }}
            </template>
          </v-select>
        </div>
      </div>
    </v-card-title>
    <CoursesDataTable
      :courses="courses"
      :include-room-column="true"
      :message-for-courses="courses.length ? (courses.length === 1 ? '' : `${courses.length} courses`) : 'No courses'"
      :on-toggle-opt-out="onToggleOptOut"
      :refreshing="isRefreshing"
      :search-text="searchText"
    />
  </v-card>
</template>

<script setup>
import {each, keys, map} from 'lodash'
import {mdiAutoFix, mdiInformationOutline, mdiMagnify} from '@mdi/js'
import {onMounted, ref} from 'vue'
import {alertScreenReader, getCourseCodes} from '@/lib/utils'
import CoursesDataTable from '@/components/course/CoursesDataTable'
import PageTitle from '@/components/util/PageTitle'
import {downloadCSV, getCourses} from '@/api/course'
import {useContextStore} from '@/stores/context'

const contextStore = useContextStore()
const courses = ref([])
const isDownloading = ref(false)
const isRefreshing = ref(false)
const searchText = ref('')
const selectedFilter = ref('Scheduled')

onMounted(() => {
  refresh().then(() => {
    contextStore.loadingComplete()
  })
})

const onClickDownload = () => {
  isDownloading.value = true
  downloadCSV(selectedFilter.value, contextStore.config.currentTermId).then(() => {
    contextStore.snackbarOpen('The CSV file has been downloaded.')
    isDownloading.value = false
  })
}

const onToggleOptOut = course => {
  if (!course.hasOptedOut && selectedFilter.value === 'Do Not Email') {
    let indexOf = courses.value.findIndex(c => c.sectionId === course.sectionId)
    if (indexOf >= 0) {
      courses.value.splice(indexOf, 1)
    }
    contextStore.snackbarOpen(`${course.label} removed from list.`)
  }
}

const refresh = srAlert => {
  isRefreshing.value = true
  return getCourses(selectedFilter.value, contextStore.config.currentTermId).then(data => {
    courses.value = data
    each(courses.value, course => {
      // In support of search, we index nested course data
      course.courseCodes = getCourseCodes(course)
      course.instructorNames = map(course.instructors, 'name')
      course.isSelectable = !course.hasOptedOut
    })
    isRefreshing.value = false
    if (srAlert) {
      alertScreenReader(srAlert)
    }
  })
}
</script>
