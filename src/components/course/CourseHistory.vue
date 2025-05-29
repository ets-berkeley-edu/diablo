<template>
  <v-card id="update-history" class="border-sm">
    <v-card-title>
      <h2>Update history</h2>
    </v-card-title>
    <v-card-text class="px-0">
      <v-data-table
        id="update-history-table"
        :headers="headers"
        density="comfortable"
        :items="history"
        :items-per-page="100"
        :page.sync="pageCurrent"
        :sort-by="[sortBy]"
        @update:sort-by="onUpdateSortBy"
      >
        <template #headers="{columns, isSorted, toggleSort, getSortIcon}">
          <tr>
            <th
              v-for="(column, index) in columns"
              :id="`update-history-${column.value}-th`"
              :key="index"
              :aria-label="column.title"
              :aria-sort="isSorted(column) ? `${sortBy.order}ending` : null"
              class="text-start text-no-wrap px-4 py-2"
              :class="column.class"
              scope="col"
            >
              <template v-if="history.length >= 2">
                <v-btn
                  :id="`update-history-sort-by-${column.value}-btn`"
                  :append-icon="getSortIcon(column)"
                  :aria-label="`Sort by ${column.title} ${isSorted(column) && sortBy.order === 'asc' ? 'descending' : 'ascending'}`"
                  class="font-size-12 font-weight-bold height-unset min-width-unset pa-1 text-transform-unset v-table-sort-btn-override"
                  :class="{'icon-visible': sortBy[0] === column.value}"
                  color="body"
                  density="compact"
                  variant="plain"
                  @click="() => toggleSort(column)"
                >
                  {{ column.title }}
                </v-btn>
              </template>
              <template v-if="history.length < 2">
                <span class="font-size-12 font-weight-bold py-1 text-align-center text-medium-emphasis text-transform-unset v-btn" :class="{'opacity-30': refreshing}">
                  {{ column.title }}
                </span>
              </template>
            </th>
          </tr>
        </template>
        <template #body="{items}">
          <tr v-if="!items.length" class="py-5 text-center text-subtitle-1">
            <td id="course-history-no-data" :colspan="headers.length">
              No updates.
            </td>
          </tr>
          <tr v-for="(item, index) in items" :key="index" class="border-b-sm">
            <td :id="`update-fieldName-${item.id}`" class="px-4 py-2" columnheader="update-history-fieldName-th">
              <span aria-hidden="true">{{ item.fieldName || '&mdash;' }}</span>
              <span class="sr-only">{{ item.fieldName || 'blank' }}</span>
            </td>
            <td :id="`update-fieldValueOld-${item.id}`" class="px-4 py-2" columnheader="update-history-fieldValueOld-th">
              <span aria-hidden="true">{{ item.fieldValueOld || '&mdash;' }}</span>
              <span class="sr-only">{{ item.fieldValueOld || 'blank' }}</span>
            </td>
            <td :id="`update-fieldValueNew-${item.id}`" class="px-4 py-2" columnheader="update-history-fieldValueNew-th">
              <span aria-hidden="true">{{ item.fieldValueNew || '&mdash;' }}</span>
              <span class="sr-only">{{ item.fieldValueNew || 'blank' }}</span>
            </td>
            <td :id="`update-requestedByName-${item.id}`" class="px-4 py-2" columnheader="update-history-requestedByName-th">
              <span aria-hidden="true">{{ item.requestedByName ? `${item.requestedByName} (${item.requestedByUid})` : '&mdash;' }}</span>
              <span class="sr-only">{{ item.requestedByName ? `${item.requestedByName} (${item.requestedByUid})` : 'blank' }}</span>
            </td>
            <td :id="`update-requestedAt-${item.id}`" class="px-4 py-2" columnheader="update-history-requestedAt-th">
              <span aria-hidden="true">{{ new Date(item.requestedAt).toLocaleString() || '&mdash;' }}</span>
              <span class="sr-only">{{ new Date(item.requestedAt).toLocaleString() || 'blank' }}</span>
            </td>
            <td :id="`update-publishedAt-${item.id}`" class="px-4 py-2" columnheader="update-history-publishedAt-th">
              <span aria-hidden="true">{{ item.publishedAt ? new Date(item.publishedAt).toLocaleString() : '&mdash;' }}</span>
              <span class="sr-only">{{ item.publishedAt ? new Date(item.publishedAt).toLocaleString() : 'blank' }}</span>
            </td>
            <td :id="`update-status-${item.id}`" class="px-4 py-2" columnheader="update-history-status-th">
              <span aria-hidden="true">{{ item.status || '&mdash;' }}</span>
              <span class="sr-only">{{ item.status || 'blank' }}</span>
            </td>
          </tr>
        </template>
        <template #bottom="{pageCount}">
          <div v-if="pageCount > 1" class="text-center pb-4 pt-2">
            <v-pagination
              id="update-history-pagination"
              v-model="pageCurrent"
              :length="pageCount"
            ></v-pagination>
          </div>
        </template>
      </v-data-table>
    </v-card-text>
  </v-card>
</template>

<script setup>
import {find, get} from 'lodash'
import {ref} from 'vue'
import {alertScreenReader} from '@/lib/utils'

defineProps({
  history: {
    required: true,
    type: Array
  }
})

const pageCurrent = ref(1)
const sortBy = ref({key: '', order: ''})
const headers = ref([
  {title: 'Field', value: 'fieldName'},
  {title: 'Old Value', value: 'fieldValueOld'},
  {title: 'New Value', value: 'fieldValueNew'},
  {title: 'Requested by', value: 'requestedByName'},
  {title: 'Requested at', value: 'requestedAt'},
  {title: 'Published at', value: 'publishedAt'},
  {title: 'Status', value: 'status'}
])

const onUpdateSortBy = primarySortBy => {
  const key = get(primarySortBy, '0.key')
  pageCurrent.value = 1
  if (key) {
    const header = find(headers.value, {value: key})
    sortBy.value = primarySortBy[0]
    if (header) {
      alertScreenReader(`Sorted by ${header.title}, ${sortBy.value.order}ending`)
    }
  } else {
    sortBy.value = {key: '', order: ''}
    alertScreenReader('Unsorted')
  }
}

</script>
