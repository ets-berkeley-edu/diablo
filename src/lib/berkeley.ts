import {find, startsWith} from 'lodash'
import type {Course, Meeting} from '@/lib/types'

export function findInstructor(course: Course, uid: string) {
  const instructor = find(course.instructors, ['uid', uid])
  if (!instructor) {
    throw Error(`Course ${course.sectionId} (${getTermName(course.termId)}) has no instructor where UID = ${uid}`)
  }
  return instructor
}

export function getCourseCodes(course: Course) {
  return course.label.split('|').map((l: string) => l.trim())
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
