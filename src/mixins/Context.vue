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
      if (courses.length > 1) {
        let message = `${courses.length} course${courses.length === 1 ? '' : 's'}`
        const scheduled = this.$_.filter(courses, 'scheduled')
        if (scheduled && scheduled.length) {
          return `${message}. ${scheduled.length} ${scheduled.length === 1 ? 'has' : 'have'} recordings scheduled.`
        } else {
          return message
        }
      } else {
        return ''
      }
    }
  }
}
</script>
