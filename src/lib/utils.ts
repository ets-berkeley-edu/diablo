import {nextTick} from 'vue'
import {useContextStore} from '@/stores/context'

export function alertScreenReader(message: string) {
  const store = useContextStore()
  store.alertScreenReader('')
  nextTick(() => store.alertScreenReader(message))
}

export function putFocusNextTick(id: string, {scroll=true, scrollBlock='center', cssSelector=undefined}: {scroll?: boolean, scrollBlock?: 'start' | 'center' | 'end' | 'nearest', cssSelector?: string}={}) {
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