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
    ])
  }
}
</script>
