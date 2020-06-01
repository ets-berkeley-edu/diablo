<template>
  <v-card v-if="!loading" outlined class="elevation-1">
    <v-card-title class="align-start p-3">
      <div class="pt-2">
        <h1><v-icon class="pb-2" large>mdi-auto-fix</v-icon> The Ouija Board</h1>
      </div>
      <v-spacer></v-spacer>
      <div class="float-right w-50">
        <v-text-field
          id="input-search"
          v-model="searchText"
          append-icon="mdi-magnify"
          clearable
          label="Search"
          single-line
          hide-details
        ></v-text-field>
        <div class="d-flex">
          <v-select
            id="ouija-filter-options"
            v-model="selectedFilter"
            color="secondary"
            :items="$_.keys($config.searchFilterOptions)"
            @change="refresh"
          >
            <span :id="`filter-option-${data.item.value}`" slot="item" slot-scope="data">{{ data.item }}</span>
            <template v-slot:selection="{ item }">
              <v-tooltip id="tooltip-ouija-filter" bottom>
                <template v-slot:activator="{ on }">
                  <v-icon
                    slot="prepend-item"
                    class="pb-1 pr-2"
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
      :message-for-courses="getMessageForCourses()"
      :on-toggle-opt-out="onToggleOptOut"
      :refreshing="refreshing"
      :search-text="searchText"
    />
  </v-card>
</template>

<script>
  import CoursesDataTable from '@/components/course/CoursesDataTable'
  import Context from '@/mixins/Context'
  import Utils from '@/mixins/Utils'
  import {getCourses} from '@/api/course'

  export default {
    name: 'Ouija',
    components: {CoursesDataTable},
    mixins: [Context, Utils],
    data: () => ({
      courses: undefined,
      refreshing: undefined,
      searchText: '',
      selectedFilter: 'Not Invited'
    }),
    created() {
      this.$loading()
      this.refresh()
    },
    methods: {
      getMessageForCourses() {
        return this.summarize(this.courses)
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
        const done = () => {
          this.refreshing = false
          this.$ready('Ouija Board')
        }
        this.refreshing = true
        getCourses(this.selectedFilter, this.$config.currentTermId).then(data => {
          this.courses = data
          this.$_.each(this.courses, course => {
            // In support of search, we index nested course data
            course.instructorNames = this.$_.map(course.instructors, 'name')
            course.publishTypeNames = course.approvals.length ? this.$_.last(course.approvals).publishTypeName : null
            course.isSelectable = !course.hasOptedOut
          })
          done()
        }).catch(done)
      }
    }
  }
</script>
