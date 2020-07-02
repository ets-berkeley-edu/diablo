<template>
  <v-card v-if="!loading" outlined class="elevation-1">
    <v-card-title class="align-start p-3">
      <div class="pt-2">
        <h1><v-icon class="pb-2" large>mdi-candle</v-icon> The Attic</h1>
      </div>
    </v-card-title>
    <div class="ma-3 pt-3">
      <h2>Report</h2>
      <v-data-table
        disable-pagination
        :headers="[
          {text: 'Key', value: 'key'},
          {text: 'Value', value: 'value'}
        ]"
        hide-default-footer
        :items="coursesReport"
      ></v-data-table>
    </div>
    <div class="ma-3 pt-3">
      <h2>Admin Users</h2>
      <v-data-table
        disable-pagination
        :headers="[
          {text: 'Name', value: 'name'},
          {text: 'Email', value: 'email'},
          {text: 'UID', value: 'uid'}
        ]"
        hide-default-footer
        :items="adminUsers"
      ></v-data-table>
    </div>
    <div class="ma-3">
      <Configs />
    </div>
  </v-card>
</template>

<script>
  import Configs from '@/components/attic/Configs'
  import Context from '@/mixins/Context'
  import Utils from '@/mixins/Utils'
  import {getAdminUsers} from '@/api/user'
  import {getCoursesReport} from '@/api/course'

  export default {
    name: 'Attic',
    components: {Configs},
    mixins: [Context, Utils],
    data: () => ({
      adminUsers: undefined,
      coursesReport: undefined
    }),
    created() {
      this.$loading()
      getCoursesReport(this.$config.currentTermId).then(report => {
        this.coursesReport = []
        this.$_.each(report, (value, key) => {
          this.coursesReport.push({key: this.decamelize(key), value})
        })
        this.coursesReport = this.$_.sortBy(this.coursesReport, ['key'])

        getAdminUsers().then(data => {
          this.adminUsers = data
          this.$ready('Attic')
        })
      })
    },
    methods: {
    }
  }
</script>
