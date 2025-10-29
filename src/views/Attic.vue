<template>
  <v-card v-if="!contextStore.loading" elevation="0">
    <v-card-title>
      <PageTitle :icon="mdiCandle" text="The Attic" />
    </v-card-title>
    <div class="pa-3">
      <h2>Report</h2>
      <v-data-table
        :headers="[
          {title: 'Key', value: 'key'},
          {title: 'Value', value: 'value'}
        ]"
        hide-default-footer
        :items="coursesReport"
        :items-per-page="-1"
      />
    </div>
    <div class="ma-3 pt-3">
      <h2>Admin Users</h2>
      <v-data-table
        :headers="[
          {title: 'Name', value: 'name'},
          {title: 'Email', value: 'email'},
          {title: 'UID', value: 'uid'}
        ]"
        hide-default-footer
        :items="adminUsers"
        :items-per-page="-1"
      />
    </div>
    <Configs class="ma-3" />
  </v-card>
</template>

<script setup>
import {each, sortBy} from 'lodash'
import {mdiCandle} from '@mdi/js'
import {onMounted, ref} from 'vue'
import Configs from '@/components/attic/Configs'
import {decamelize} from '@/lib/utils'
import {getAdminUsers} from '@/api/user'
import {getCoursesReport} from '@/api/course'
import PageTitle from '@/components/util/PageTitle'
import {useContextStore} from '@/stores/context'


const adminUsers = ref([])
const contextStore = useContextStore()
const coursesReport = ref([])

contextStore.loadingStart()

onMounted(() => {
  getCoursesReport(contextStore.config.currentTermId).then(report => {
    each(report, (value, key) => {
      coursesReport.value.push({key: decamelize(key.toString()), value})
    })
    coursesReport.value = sortBy(coursesReport.value, ['key'])

    getAdminUsers().then(data => {
      adminUsers.value = data
      contextStore.loadingComplete()
    })
  })
})
</script>
