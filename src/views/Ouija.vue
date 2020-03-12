<template>
  <div>
    <div class="pl-3">
      <h2><v-icon class="pb-3" large>mdi-auto-fix</v-icon> The Ouija Board</h2>
    </div>
    <v-data-table
      :headers="headers"
      :hide-default-footer="true"
      :items="sections"
      :items-per-page="100"
      :loading="loading"
      class="elevation-1"
    >
      <template v-slot:top>
        Hello World
      </template>
      <template v-slot:body="{ items }">
        <tbody>
          <tr v-for="item in items" :key="item.name">
            <td class="text-no-wrap">{{ item.courseName }}</td>
            <td class="text-no-wrap">{{ item.sectionId }}</td>
          </tr>
        </tbody>
      </template>
    </v-data-table>
  </div>
</template>

<script>
  import Loading from '@/mixins/Loading'
  import {getAllApprovals} from '@/api/approval'

  export default {
    name: 'Ouija',
    mixins: [Loading],
    data: () => ({
      sections: undefined,
      headers: [
        {text: 'Course', value: 'courseName'},
        {text: 'Section id', value: 'sectionId', sortable: false}
      ]
    }),
    created() {
      getAllApprovals(this.$config.currentTermId).then(data => {
        this.sections = data
        this.loaded()
      })
    }
  }
</script>
