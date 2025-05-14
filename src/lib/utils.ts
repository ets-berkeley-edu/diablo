import {filter, split} from 'lodash'
import {nextTick} from 'vue'
import {useContextStore} from '@/stores/context'
import type ScrollLogicalPosition from 'typescript'

export function alertScreenReader(message: string) {
  const store = useContextStore()
  store.alertScreenReader('')
  nextTick(() => store.alertScreenReader(message))
}

export function getCourseCodes(course) {
  return course.label.split('|').map((l: string) => l.trim())
}

export function getDisplayMeetings(course) {
  if (course.meetings.eligible.length) {
    return course.meetings.eligible
  } else {
    return course.meetings.ineligible
  }
}

export function putFocusNextTick(id: string, {scroll=true, scrollBlock='center', cssSelector=undefined}: {scroll?: boolean, scrollBlock?: ScrollLogicalPosition, cssSelector?: string}={}) {
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

export function summarize(courses) {
  const total = courses.length
  let msg = `${total} course${total === 1 ? '' : 's'}.`
  const scheduled = filter(courses, 'scheduled')
  if (scheduled.length) {
    msg += ` ${scheduled.length} ${scheduled.length === 1 ? 'has' : 'have'} recordings scheduled.`
  }
  return msg
}
