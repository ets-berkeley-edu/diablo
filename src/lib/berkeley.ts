import {get, startsWith} from 'lodash'
import type {Course, Meeting} from '@/lib/types'

export function describeRecordingsStatus(status: string | undefined) {
  if (status === 'Pending') {
    return 'Recordings will be scheduled within an hour.'
  } else if (status === 'Not Scheduled') {
    return 'Recordings are not scheduled. One or more instructors have not opted in.'
  } else if (status === 'Partial Opt-in') {
    return 'Recordings are not scheduled. At least one instructor has not opted in.'
  } else {
    return status
  }
}

export function getCourseCodes(course: Course) {
  return course.label.split('|').map((l: string) => l.trim())
}

export function getCourseStatusLabel(course: Course) {
  const eligibleLen = get(course, 'meetings.eligible.length', 0)
  const instructors = get(course, 'instructors', []) || []
  const totalInstructors = instructors.length
  const optedInCount = instructors.filter(i => i?.hasOptedIn).length
  const anyOpted = optedInCount > 0
  const allOpted = totalInstructors > 0 && optedInCount === totalInstructors
  const partialOptIn = totalInstructors > 1 && anyOpted && !allOpted
  return course.deletedAt
      ? 'Canceled'
      : (isCourseScheduled(course)
        ? 'Scheduled'
        : (eligibleLen > 0
          ? (partialOptIn
            ? 'Partial Opt-in'
            : (allOpted ? 'Pending' : 'Not Scheduled'))
          : 'Not Eligible'))
}

export function getDisplayMeetings(course: Course): Meeting[] {
  if (course.meetings.eligible.length) {
    return course.meetings.eligible
  } else {
    return course.meetings.ineligible
  }
}

export function getTermName(termId: number) {
  const id = termId.toString()
  let termName: string = ''
  if (id.length === 4) {
    const seasons = {
      '0': 'Winter',
      '2': 'Spring',
      '5': 'Summer',
      '8': 'Fall',
    }
    termName = `${seasons[id.slice(3, 4)]} ${startsWith(id, '1') ? '19' : '20'}${id.slice(1, 3)}`
  }
  return termName
}

export function isCourseScheduled(course: Course) {
  return Array.isArray(course.scheduled) ? course.scheduled.length > 0 : !!course.scheduled
}

