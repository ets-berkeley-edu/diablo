<script>
import {nextTick} from 'vue'
import _ from 'lodash'
import {useContextStore} from '@/stores/context'

export default {
  name: 'Context',
  computed: {
    loading() {
      return useContextStore().loading
    },
    screenReaderAlert() {
      return useContextStore().screenReaderAlert
    },
    snackbar() {
      return useContextStore().snackbar
    },
    snackbarShow: {
      get() {
        return useContextStore().snackbarShow
      },
      set(show) {
        const store = useContextStore()
        show ? store.snackbarOpen('') : store.snackbarClose()
      }
    }
  },
  methods: {
    alertScreenReader(message) {
      const store = useContextStore()
      store.alertScreenReader('')
      nextTick(() => store.alertScreenReader(message))
    },

    reportError(message) {
      useContextStore().snackbarReportError(message)
    },

    snackbarOpen(message) {
      useContextStore().snackbarOpen(message)
    },

    summarize(courses) {
      const total = courses.length
      let msg = `${total} course${total === 1 ? '' : 's'}.`
      const scheduled = _.filter(courses, 'scheduled')
      if (scheduled.length) {
        msg += ` ${scheduled.length} ${scheduled.length === 1 ? 'has' : 'have'} recordings scheduled.`
      }
      return msg
    }
  }
}

</script>
