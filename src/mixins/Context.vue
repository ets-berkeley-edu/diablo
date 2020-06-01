<script>
import store from '@/store'
import Vue from 'vue'
import {mapActions, mapGetters} from 'vuex'

export default {
  name: 'Context',
  computed: {
    ...mapGetters('context', ['loading', 'screenReaderAlert', 'snackbar']),
    snackbarShow: {
      get: () => store.getters['context/snackbarShow'],
      set: show => store.dispatch(show ? 'context/snackbarOpen' : 'context/snackbarClose')
    }
  },
  methods: {
    ...mapActions('context', ['snackbarClose']),
    alertScreenReader(message) {
      store.dispatch('context/alertScreenReader', '')
      Vue.nextTick(() => store.dispatch('context/alertScreenReader', message))
    },
    reportError: message => store.dispatch('context/snackbarReportError', message),
    snackbarOpen: message => store.dispatch('context/snackbarOpen', message),
    summarize(courses) {
      let message = undefined
      if (courses.length) {
        message = `${courses.length === 1 ? 'One' : courses.length} course${courses.length === 1 ? '' : 's'}`
        const scheduledCourses = this.$_.filter(courses, 'scheduled')
        if (scheduledCourses.length) {
          message += ` and ${scheduledCourses.length === 1 ? 'one has' : `${scheduledCourses.length} have`} recordings scheduled.`
        } else {
          message += ' and no recordings scheduled.'
        }
      } else {
        message = 'No courses.'
      }
      return message
    }
  }
}
</script>
