import {defineStore} from 'pinia'
import type {Course} from '@/lib/types'

const BLANK_COURSE: Partial<Course> = {
  canvasSites: [],
  collaborators: [],
  instructors: [],
  meetings: {
    eligible: [],
    ineligible: []
  },
  updateHistory: []
}

export const useCourseStore = defineStore('course', {
  state: () => ({
    course: BLANK_COURSE as Course,
    disableButtons: false
  }),
  actions: {
    setCourse(course: Course) {
      this.course = course
    },
    setDisableButtons(value: boolean) {
      this.disableButtons = value
    }
  }
})
