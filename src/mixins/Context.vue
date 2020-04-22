<script>
import store from '@/store'
import { mapActions, mapGetters } from 'vuex'

export default {
  name: 'Context',
  computed: {
    ...mapGetters('context', ['loading', 'snackbar']),
    snackbarShow: {
      get: () => store.getters['context/snackbarShow'],
      set: show => store.dispatch(show ? 'context/snackbarOpen' : 'context/snackbarClose')
    }
  },
  methods: {
    ...mapGetters('context', [
      'screenReaderAlert'
    ]),
    ...mapActions('context', [
      'alertScreenReader',
      'snackbarClose',
      'snackbarOpen',
      'snackbarReportError'
    ]),
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
