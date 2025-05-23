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
            :aria-describedby="undefined"
            aria-label="Search courses table"
            class="pb-2"
            clearable
            :disabled="isDownloading"
            hide-details
            label="Search"
            single-line
          ></v-text-field>
          <v-select
            id="ouija-filter-options"
            v-model="selectedFilter"
            aria-label="Filter courses table"
            class="pb-2"
            color="primary"
            :disabled="isDownloading"
            :item-props="true"
            :items="filterOptions"
            :list-props="{ariaLabel: 'Courses table filter options', id: 'ouija-filter-options-list'}"
            :menu-props="{attach: menuContainer, eager: true, id: 'ouija-filter-options-menu'}"
            @update:menu="isOpen => putFocusNextTick(isOpen ? 'filter-option-scheduled' : 'ouija-filter-options')"
            @update:model-value="refresh"
          >
            <template #item="{props: itemProps, item}">
              <v-list-item :id="`filter-option-${kebabCase(item.value)}`" v-bind="itemProps" :subtitle="item.raw.subtitle">
                <template #title="{title}">{{ title }}<span class="sr-only">: </span></template>
              </v-list-item>
            </template>
          </v-select>
          <div id="ouija-filter-options-menu-container" ref="menuContainer"></div>
        </v-col>
      </v-row>
    </v-card-title>
    <CoursesDataTable
      :courses="courses"
      :description="coursesTableDescription"
      :include-room-column="true"
      :on-toggle-opt-out="onToggleOptOut"
      :refreshing="isRefreshing"
      :search-text="searchText"
    />
  </v-card>
</template>

<script setup>
import {computed, onMounted, ref} from 'vue'
import {each, kebabCase, map} from 'lodash'
import {mdiAutoFix, mdiMagnify} from '@mdi/js'
import {alertScreenReader, getCourseCodes, pluralize, putFocusNextTick} from '@/lib/utils'
import CoursesDataTable from '@/components/course/CoursesDataTable'
import PageTitle from '@/components/util/PageTitle'
import {downloadCSV, getCourses} from '@/api/course'
import {useContextStore} from '@/stores/context'

const contextStore = useContextStore()
const courses = ref([])
const filterOptions = map(contextStore.config.searchFilterOptions, (v, k) => {
  return {title: k, subtitle: v}
})
const isDownloading = ref(false)
const isRefreshing = ref(false)
const menuContainer = ref()
const searchText = ref('')
const selectedFilter = ref('Scheduled')
const coursesTableDescription = computed(() => {
  const pluralized = pluralize('course', courses.value.length, {includeCount: false})
  const description = `${courses.value.length ? courses.value.length.toLocaleString() : 'No'} ${selectedFilter.value || ''} ${pluralized}`
  if (selectedFilter.value === 'No Instructors') {
    return description.replace(`No Instructors ${pluralized}`, `${pluralized} with no instructor`)
  } else if (selectedFilter.value === 'All') {
    return description.replace(`All ${pluralized}`, pluralized)
  }
  else {
    return description
  }
})

onMounted(() => {
  contextStore.loadingStart()
  loadCourses().then(() => {
    contextStore.loadingComplete('Ouija Board', `Showing ${coursesTableDescription.value}`)
  })
})

const loadCourses = () => {
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
  })
}

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

const refresh = () => {
  alertScreenReader('Refreshing courses table')
  loadCourses().then(() => {
    alertScreenReader(`Showing ${coursesTableDescription.value}`)
  })
}
</script>
