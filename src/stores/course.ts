import {defineStore} from 'pinia'
import type {Course} from '@/lib/types'
import {useContextStore} from '@/stores/context'

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
    disableButtons: false,
    displayLabels: {
      kaltura_media_gallery: 'Publish to the Media Gallery (all members of the bCourses site will have access)',
      kaltura_my_media: 'Place in My Media (I will decide if and how I want to share)',
      presenter_presentation_audio: 'Camera Without Operator',
      presenter_presentation_audio_with_operator: `Camera With Operator ($${useContextStore().config.courseCapturePremiumCost} fee)`
    }
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
