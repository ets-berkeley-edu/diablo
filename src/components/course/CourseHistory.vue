<template>
  <v-card
    id="update-history"
    aria-labelledby="update-history-header"
    class="border-sm"
    role="region"
  >
    <v-card-title>
      <h2 id="update-history-header">
        <span class="sr-only">Course </span>Update history
      </h2>
    </v-card-title>
    <v-card-text class="px-0">
      <v-data-table
        id="update-history-table"
        v-model:page="pageCurrent"
        :headers="headers"
        density="comfortable"
        :items="history"
        :items-per-page="100"
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
                  :append-icon="isSorted(column) ? getSortIcon(column) : undefined"
                  :aria-label="sortButtonAriaLabel(column, isSorted)"
                  class="font-size-13 font-weight-bold height-unset min-width-unset pa-1 text-transform-unset v-table-sort-btn-override"
                  :class="{'icon-visible': sortBy[0] === column.value}"
                  density="compact"
                  variant="plain"
                  @click="() => toggleSort(column)"
                >
                  {{ column.title }}
                </v-btn>
              </template>
              <template v-if="history.length < 2">
                <span class="font-size-13 font-weight-bold py-1 text-align-center text-medium-emphasis text-transform-unset v-btn">
                  {{ column.title }}
                </span>
              </template>
            </th>
          </tr>
        </template>
        <template #body="{items}">
          <tr v-if="!items.length" id="course-history-no-data" class="py-5 text-center text-subtitle-1">
            <td :colspan="headers.length">
              No updates.
            </td>
          </tr>
          <tr v-for="(item, index) in items" :key="index" class="border-b-sm">
            <td
              :id="`update-fieldName-${item.id}`"
              class="px-4 py-2"
              columnheader="update-history-fieldName-th"
              :data-label="labelFor('fieldName')"
            >
              <span aria-hidden="true">{{ item.fieldName || '&mdash;' }}</span>
              <span class="sr-only">{{ item.fieldName || 'blank' }}</span>
            </td>
            <td
              :id="`update-fieldValueOld-${item.id}`"
              class="px-4 py-2"
              columnheader="update-history-fieldValueOld-th"
              :data-label="labelFor('fieldValueOld')"
            >
              <span aria-hidden="true">{{ item.fieldValueOld || '&mdash;' }}</span>
              <span class="sr-only">{{ item.fieldValueOld || 'blank' }}</span>
            </td>
            <td
              :id="`update-fieldValueNew-${item.id}`"
              class="px-4 py-2"
              columnheader="update-history-fieldValueNew-th"
              :data-label="labelFor('fieldValueNew')"
            >
              <span aria-hidden="true">{{ item.fieldValueNew || '&mdash;' }}</span>
              <span class="sr-only">{{ item.fieldValueNew || 'blank' }}</span>
            </td>
            <td
              :id="`update-requestedByName-${item.id}`"
              class="px-4 py-2"
              columnheader="update-history-requestedByName-th"
              :data-label="labelFor('requestedByName')"
            >
              <span aria-hidden="true">{{ item.requestedByName ? `${item.requestedByName} (${item.requestedByUid})` : '&mdash;' }}</span>
              <span class="sr-only">{{ item.requestedByName ? `${item.requestedByName} (${item.requestedByUid})` : 'blank' }}</span>
            </td>
            <td
              :id="`update-requestedAt-${item.id}`"
              class="px-4 py-2"
              columnheader="update-history-requestedAt-th"
              :data-label="labelFor('requestedAt')"
            >
              <span aria-hidden="true">{{ new Date(item.requestedAt).toLocaleString() || '&mdash;' }}</span>
              <span class="sr-only">{{ new Date(item.requestedAt).toLocaleString() || 'blank' }}</span>
            </td>
            <td
              :id="`update-publishedAt-${item.id}`"
              class="px-4 py-2"
              columnheader="update-history-publishedAt-th"
              :data-label="labelFor('publishedAt')"
            >
              <span aria-hidden="true">{{ item.publishedAt ? new Date(item.publishedAt).toLocaleString() : '&mdash;' }}</span>
              <span class="sr-only">{{ item.publishedAt ? new Date(item.publishedAt).toLocaleString() : 'blank' }}</span>
            </td>
            <td
              :id="`update-status-${item.id}`"
              class="px-4 py-2"
              columnheader="update-history-status-th"
              :data-label="labelFor('status')"
            >
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
            />
          </div>
        </template>
      </v-data-table>
    </v-card-text>
  </v-card>
</template>

<script setup>
import {find, get} from 'lodash'
import {computed, ref} from 'vue'
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

const headerTitleByValue = computed(() =>
  headers.value.reduce((m, h) => ((m[h.value] = h.title), m), {})
)
const labelFor = key => headerTitleByValue.value[key] || ''

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
    alertScreenReader('Default sort order restored')
  }
}

const sortButtonAriaLabel = (column, isSorted) => {
  if (isSorted(column) && 'desc' === sortBy.value.order) {
    return 'Restore default sort order'
  } else {
    return `Sort by ${column.title} ${isSorted(column) && sortBy.value.order === 'asc' ? 'descending' : 'ascending'}`
  }
}
</script>

<style scoped>
@media (max-width: 941px) {
  :deep(#update-history-table .v-table__wrapper) {
    overflow-x: hidden !important;
  }

  :deep(#update-history-table thead) {
    position: absolute !important;
    width: 1px !important;
    height: 1px !important;
    margin: -1px !important;
    padding: 0 !important;
    overflow: hidden !important;
    clip: rect(1px, 1px, 1px, 1px) !important;
    border: 0 !important;
  }

  :deep(#update-history-table tbody tr) {
    display: block !important;
    border: 1px solid var(--v-theme-outline-variant);
    border-radius: 12px;
    margin: 12px;
    padding: 8px 0;
    box-shadow: 0 1px 2px rgba(0,0,0,.06);
    background: var(--v-theme-surface);
  }

  :deep(#update-history-table tbody tr.border-b-sm) {
    border-bottom: 0 !important;
  }

  :deep(#update-history-table tbody td) {
    display: grid !important;
    grid-template-columns: minmax(120px, 40%) 1fr;
    gap: 8px;
    align-items: start;
    padding: 10px 14px !important;
    border: 0 !important;
    width: 100% !important;
    box-sizing: border-box;
  }

  :deep(#update-history-table tbody td::before) {
    content: attr(data-label);
    font-weight: 600;
    opacity: .9;
  }

  :deep(#update-history-table table) {
    width: 100% !important;
    table-layout: fixed !important;
    border-collapse: separate !important;
    border-spacing: 0 !important;
  }

  :deep(#course-history-no-data) {
    display: block !important;
    margin: 12px;
    border: 1px solid var(--v-theme-outline-variant);
    border-radius: 12px;
    padding: 14px;
    text-align: center !important;
  }
}
</style>

