<template>
  <v-card
    v-if="!contextStore.loading"
    class="border-sm"
  >
    <v-card-title class="align-start">
      <v-row>
        <v-col class="pt-2" cols="12" md="6">
          <PageTitle :icon="mdiAutoFix" text="The Ouija Board" />
          <v-btn
            v-if="courses.length"
            class="ml-12 mt-2"
            :disabled="isDownloading || isRefreshing"
            variant="text"
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
        </v-col>
        <v-col class="pr-4" cols="12" md="6">
          <v-text-field
            id="input-search"
            v-model="searchText"
            :append-icon="mdiMagnify"
            aria-label="Search courses table"
            clearable
            :disabled="isDownloading"
            hide-details
            label="Search"
            single-line
            variant="underlined"
          ></v-text-field>
          <v-select
            id="ouija-filter-options"
            v-model="selectedFilter"
            aria-label="Filter courses table"
            color="secondary"
            :disabled="isDownloading"
            :items="keys(contextStore.config.searchFilterOptions)"
            variant="underlined"
            @update:model-value="() => refresh(`Courses table refreshed. Showing ${contextStore.config.searchFilterOptions[selectedFilter]}`)"
          >
            <template #item="{props: itemProps, item}">
              <v-list-item :id="`filter-option-${item.value}`" v-bind="itemProps"></v-list-item>
            </template>
            <template #selection="{item}">
              <v-tooltip id="tooltip-ouija-filter" location="bottom">
                <template #activator="{props: tooltipProps}">
                  <v-icon
                    class="pb-1 pr-2"
                    :icon="mdiInformationOutline"
                    v-bind="tooltipProps"
                  />
                </template>
                <span class="font-weight-bold">{{ selectedFilter }}:</span> {{ contextStore.config.searchFilterOptions[selectedFilter] }}
              </v-tooltip>
              {{ item.title }}
            </template>
          </v-select>
        </v-col>
      </v-row>
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
  contextStore.loadingStart()
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
