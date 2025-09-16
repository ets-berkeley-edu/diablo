import {
  capitalize,
  cloneDeep,
  concat,
  each,
  filter,
  head,
  initial,
  join,
  last,
  split,
  startsWith,
  trim,
} from 'lodash'
import {nextTick} from 'vue'
import type {Course, DiabloUser, Meeting} from '@/lib/types'
import {useContextStore} from '@/stores/context'

export const ANONYMOUS_USER: DiabloUser = {
  courses: [],
  emailAddress: null,
  id: null,
  isActive: false,
  isAdmin: false,
  isAnonymous: true,
  isAuthenticated: false,
  isExpired: true,
  isTeaching: false,
  name: 'UID None',
  uid: null
}

export function alertScreenReader(message: string) {
  const store = useContextStore()
  store.alertScreenReader('')
  nextTick(() => store.alertScreenReader(message))
}

export function decamelize(str: string, separator = ' ') {
  return capitalize(
    str
      .replace(/([a-z\d])([A-Z])/g, '$1' + separator + '$2')
      .replace(/([A-Z]+)([A-Z][a-z\d]+)/g, '$1' + separator + '$2')
  )
}

export function getCourseCodes(course: Course) {
  return course.label.split('|').map((l: string) => l.trim())
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
    termName = `${seasons[id.slice(3, 4)]} ${startsWith(id, '1') ? '19' : '20'
      }${id.slice(1, 3)}`
  }
  return termName
}

export function getDisplayMeetings(course: Course): Meeting[] {
  if (course.meetings.eligible.length) {
    return course.meetings.eligible
  } else {
    return course.meetings.ineligible
  }
}

export function oxfordJoin(arr: string[]) {
  switch (arr.length) {
    case 1:
      return head(arr)
    case 2:
      return `${head(arr)} and ${last(arr)}`
    default:
      return join(concat(initial(arr), ` and ${last(arr)}`), ', ')
  }
}

export function partitionCoursesByEligibility(
  courses: Course[],
  eligibleCourses: Course[],
  ineligibleCourses: Course[]
) {
  each(courses, (c) => {
    if (c.meetings.eligible.length) {
      eligibleCourses.push(c)
      if (c.meetings.ineligible.length) {
        const courseCopyWithIneligibleMeetings = cloneDeep(c)
        courseCopyWithIneligibleMeetings.meetings.eligible = []
        courseCopyWithIneligibleMeetings.scheduled = null
        ineligibleCourses.push(courseCopyWithIneligibleMeetings)
      }
    } else {
      ineligibleCourses.push(c)
    }
  })
}

export function pluralize(noun: string, count: number, includeCount = true) {
  const countOf = includeCount ? `${count} ` : ''
  const desc = count !== 1 ? `${noun}s` : noun
  return `${countOf}${desc}`
}

export function putFocusNextTick(
  id: string,
  {
    scroll = true,
    scrollBlock = 'center',
    cssSelector = undefined,
  }: {
    scroll?: boolean
    scrollBlock?: ScrollLogicalPosition
    cssSelector?: string
  } = {}
) {
  nextTick(() => {
    let counter = 0
    const putFocus = setInterval(() => {
      let el = document.getElementById(id)
      el = el && cssSelector ? el.querySelector(cssSelector) : el
      if (el) {
        el.classList.add('scroll-margins')
        el.focus()
        if (scroll) {
          el.scrollIntoView({behavior: 'smooth', block: scrollBlock})
        }
      }
      if (el || ++counter > 5) {
        // Abort after success or five attempts
        clearInterval(putFocus)
      }
    }, 500)
  })
}

export function stripAnchorRef(path: string) {
  return split(path, '#', 1)[0]
}

export function stripHtmlAndTrim(html: string) {
  let text = html && html.replace(/<([^>]+)>/gi, '')
  text = text && text.replace(/&nbsp;/g, '')
  return trim(text)
}

export function summarize(courses: Course[]) {
  const total = courses.length
  let msg = `${total} course${total === 1 ? '' : 's'}.`
  const scheduled = filter(courses, 'scheduled')
  if (scheduled.length) {
    msg += ` ${scheduled.length} ${scheduled.length === 1 ? 'has' : 'have'
      } recordings scheduled.`
  }
  return msg
}

export function escapeForRegExp(s: string) {
  return s && s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}
