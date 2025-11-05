<template>
  <v-card
    v-if="!contextStore.loading"
    class="ouija-card"
    elevation="0"
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
            />
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
          />
          <v-select
            id="ouija-filter-options"
            v-model="ouijaStore.filter"
            aria-label="Filter courses table"
            autocomplete="off"
            class="pb-2"
            color="primary"
            :disabled="isDownloading"
            item-props
            :items="filterOptions"
            :list-props="{ariaLabel: 'Filter courses table', ariaLive: 'off', id: 'ouija-filter-options-list'}"
            :menu-props="{attach: menuContainer, eager: true, id: 'ouija-filter-options-menu'}"
            :title="undefined"
            @update:menu="onToggleFilterOptionsMenu"
            @update:model-value="refresh"
          >
            <template #selection="{item}">
              {{ item.value }}
            </template>
            <template #item="{props: itemProps, item}">
              <v-list-item
                :id="`filter-option-${kebabCase(item.value)}`"
                v-bind="itemProps"
                role="option"
                :subtitle="item.raw.subtitle"
              >
                <template #title="{title}">{{ title }}<span class="sr-only">: </span></template>
              </v-list-item>
            </template>
          </v-select>
          <div id="ouija-filter-options-menu-container" ref="menuContainer" />
        </v-col>
      </v-row>
    </v-card-title>
    <CoursesDataTable
      v-model:page="ouijaStore.pageNumber"
      v-model:sort-by="ouijaStore.sortBy"
      :courses="courses"
      :description="coursesTableDescription"
      :include-room-column="true"
      :refreshing="isRefreshing"
      :search-text="searchText"
      :show-opt-in="true"
    />
  </v-card>
</template>

<script lang="ts" setup>
import {computed, onMounted, onUnmounted, ref} from 'vue'
import {each, kebabCase, map} from 'lodash'
import {mdiAutoFix, mdiMagnify} from '@mdi/js'
import type {CourseSortable} from '@/lib/types'
import {OuijaFilter, useOuijaStore} from '@/stores/ouija'
import {getCourseCodes} from '@/lib/berkeley'
import {alertScreenReader, pluralize, putFocusNextTick} from '@/lib/utils'
import {downloadCSV, getCourses} from '@/api/course'
import {useContextStore} from '@/stores/context'
import CoursesDataTable from '@/components/course/CoursesDataTable.vue'
import PageTitle from '@/components/util/PageTitle.vue'

const contextStore = useContextStore()
const courses = ref<CourseSortable[]>([])
const filterOptions = map(contextStore.config.searchFilterOptions, (v, k) => {
  return {title: k, subtitle: v}
})
const isDownloading = ref(false)
const isRefreshing = ref(false)
const menuContainer = ref()
const ouijaStore = useOuijaStore()
const searchText = ref('')
const coursesTableDescription = computed(() => {
  const pluralized = pluralize('course', courses.value.length, false)
  let description = `${courses.value.length ? courses.value.length.toLocaleString() : 'No'} ${ouijaStore.filter || ''} ${pluralized}`
  if (ouijaStore.filter === OuijaFilter.NoInstructors) {
    description = description.replace(`No Instructors ${pluralized}`, `${pluralized} with no instructor`)
  } else if (ouijaStore.filter === OuijaFilter.All) {
    description = description.replace(`All ${pluralized}`, pluralized)
  }
  return description
})

contextStore.loadingStart()

onMounted(() => {
  contextStore.setEventHandler('sidebar-navigation-click', onSidebarNavigationClick)
  loadCourses().then(() => {
    contextStore.loadingComplete('Ouija Board', `Showing ${coursesTableDescription.value}`)
  })
})

onUnmounted(() => {
  contextStore.removeEventHandler('sidebar-navigation-click', onSidebarNavigationClick)
})

const onSidebarNavigationClick = () => {
  if (!contextStore.loading) {
    useOuijaStore().$reset()
    refresh()
  }
}

const loadCourses = () => {
  isRefreshing.value = true
  return getCourses(ouijaStore.filter, contextStore.config.currentTermId).then(data => {
    courses.value = data
    each(courses.value, course => {
      // In support of search, we index nested course data
      course.courseCodes = getCourseCodes(course)
      course.instructorNames = map(course.instructors, 'name')
      course.isSelectable = course.hasOptedIn
    })
    isRefreshing.value = false
  })
}

const onClickDownload = () => {
  isDownloading.value = true
  downloadCSV(ouijaStore.filter, contextStore.config.currentTermId).then(() => {
    contextStore.snackbarOpen('The CSV file has been downloaded.')
    isDownloading.value = false
  })
}

const onToggleFilterOptionsMenu = isOpen => {
  if (isOpen) {
    putFocusNextTick('filter-option-all')
  }
}

const refresh = () => {
  ouijaStore.setPageNumber(1)
  alertScreenReader('Refreshing courses table')
  loadCourses().then(() => {
    alertScreenReader(`Showing ${coursesTableDescription.value}`)
  })
}
</script>

<style scoped>
.ouija-card {
  overflow: visible;
}
</style>
