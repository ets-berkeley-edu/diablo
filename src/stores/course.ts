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
    capability: undefined as undefined | string,
    course: BLANK_COURSE as Course,
    disableButtons: false,
    displayLabels: {
      kaltura_media_gallery: 'Publish to the Media Gallery (all members of the bCourses site will have access)',
      kaltura_my_media: 'Place in My Media (I will decide if and how I want to share)',
      presenter_presentation_audio: 'Camera Without Operator',
      presenter_presentation_audio_with_operator: `Camera With Operator ($${useContextStore().config.courseCapturePremiumCost} fee)`
    },
    hasValidMeetingTimes: false,
    isCurrentTerm: false,
    isEligibleForCourseCapture: false,
    location: undefined as undefined | string
  }),
  getters: {
    updatesQueued: (state): boolean => {
      return !!(state.course && state.course.updateHistory && state.course.updateHistory.find(u => u.status === 'queued'))
    }
  },
  actions: {
    setCourse(course: Course) {
      this.course = course
      const eligible = this.course.meetings.eligible
      const meeting = eligible[0] || this.course.meetings.ineligible[0]
      this.capability = meeting.room?.capability
      this.location = meeting.room?.location
      this.hasValidMeetingTimes = eligible.some(m => m.startDate && m.startTime && m.endDate && m.endTime)
      this.isCurrentTerm = this.course.termId === useContextStore().config.currentTermId
      this.isEligibleForCourseCapture = this.isCurrentTerm && !!this.capability && this.hasValidMeetingTimes
      if (this.isEligibleForCourseCapture) {
        if (!this.course.publishType) {
          this.course.publishType = 'kaltura_my_media'
        }
        if (!this.course.recordingType) {
          this.course.recordingType = 'presenter_presentation_audio'
        }
      }
    },
    setDisableButtons(value: boolean) {
      this.disableButtons = value
    }
  }
})
