<template>
  <v-card v-if="!loading" outlined class="elevation-1">
    <v-card-title class="align-start">
      <div class="pt-2">
        <PageTitle icon="mdi-auto-fix" text="The Ouija Board" />
        <v-btn
          v-if="courses.length"
          class="ml-8"
          :disabled="isDownloading || refreshing"
          text
          @click="downloadCSV"
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
          append-icon="mdi-magnify"
          clearable
          :disabled="isDownloading"
          label="Search"
          single-line
          hide-details
        ></v-text-field>
        <div class="d-flex">
          <v-select
            id="ouija-filter-options"
            v-model="selectedFilter"
            color="secondary"
            :disabled="isDownloading"
            :items="$_.keys($config.searchFilterOptions)"
            @change="refresh"
          >
            <span :id="`filter-option-${data.item.value}`" slot="item" slot-scope="data">{{ data.item }}</span>
            <template #selection="{item}">
              <v-tooltip id="tooltip-ouija-filter" bottom>
                <template #activator="{on, attrs}">
                  <v-icon
                    slot="prepend-item"
                    class="pb-1 pr-2"
                    v-bind="attrs"
                    v-on="on"
                  >
                    mdi-information-outline
                  </v-icon>
                </template>
                <span class="font-weight-bold">{{ selectedFilter }}:</span> {{ $config.searchFilterOptions[selectedFilter] }}
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
      :refreshing="refreshing"
      :search-text="searchText"
    />
  </v-card>
</template>

<script>
import CoursesDataTable from '@/components/course/CoursesDataTable'
import Context from '@/mixins/Context'
import PageTitle from '@/components/util/PageTitle'
import Utils from '@/mixins/Utils'
import {downloadCSV, getCourses} from '@/api/course'

export default {
  name: 'Ouija',
  mixins: [Context, Utils],
  components: {CoursesDataTable, PageTitle},
  data: () => ({
    courses: undefined,
    isDownloading: false,
    refreshing: undefined,
    searchText: '',
    selectedFilter: 'Not Invited'
  }),
  created() {
    this.$loading()
    this.refresh().then(() => {
      this.$ready('Ouija Board')
    })
  },
  methods: {
    downloadCSV() {
      this.isDownloading = true
      downloadCSV(this.selectedFilter, this.$config.currentTermId).then(() => {
        this.snackbarOpen('The CSV file has been downloaded.')
        this.isDownloading = false
      })
    },
    onToggleOptOut(course) {
      if (!course.hasOptedOut && this.selectedFilter === 'Do Not Email') {
        let indexOf = this.courses.findIndex(c => c.sectionId === course.sectionId)
        if (indexOf >= 0) {
          this.courses.splice(indexOf, 1)
        }
        this.snackbarOpen(`${course.label} removed from list.`)
      }
    },
    refresh() {
      this.refreshing = true
      return getCourses(this.selectedFilter, this.$config.currentTermId).then(data => {
        this.courses = data
        this.$_.each(this.courses, course => {
          // In support of search, we index nested course data
          course.courseCodes = this.getCourseCodes(course)
          course.instructorNames = this.$_.map(course.instructors, 'name')
          course.publishTypeNames = course.approvals.length ? this.$_.last(course.approvals).publishTypeName : null
          course.isSelectable = !course.hasOptedOut
        })
        this.refreshing = false
      })
    }
  }
}
</script>
