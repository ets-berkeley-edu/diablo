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
  toLower,
  trim,
} from 'lodash'
import {nextTick} from 'vue'
import type {Course, DiabloUser} from '@/lib/types'
import {useContextStore} from '@/stores/context'

export const ANONYMOUS_USER: DiabloUser = {
  id: undefined,
  courses: [],
  doNotEmail: true,
  emailAddress: null,
  isActive: false,
  isAdmin: false,
  isAnonymous: true,
  isAuthenticated: false,
  isExpired: true,
  isTeaching: false,
  name: 'UID None',
  optInNewCourses: false,
  uid: undefined
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

export function escapeForRegExp(s: string) {
  return s && s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

export function normalizeId(id: string) {
  return toLower(id).replace(/\W/g, ' ').trim().replace(/[ _]+/g, '-')
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
