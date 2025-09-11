import {defineStore} from 'pinia'
import type {SortBy} from '@/lib/types'

export enum OuijaFilter {
  All = 'All',
  Eligible = 'Eligible',
  EligibleUnscheduled = 'Eligible Unscheduled',
  NoInstructors = 'No Instructors',
  OptedOut = 'Opted Out',
  PartiallyApproved = 'Partially Approved',
  Scheduled = 'Scheduled'
}

export const useOuijaStore = defineStore('ouija', {
  state: () => ({
    filter: OuijaFilter.All,
    pageNumber: 1,
    sortBy: {} as SortBy
  }),
  actions: {
    setFilter(filter: OuijaFilter) {
      this.filter = filter
    },
    setPageNumber(pageNumber: number) {
      this.pageNumber = pageNumber
    }
  }
})
