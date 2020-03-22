<script>
import { mapActions, mapGetters } from 'vuex'

export default {
  name: 'Context',
  computed: {
    ...mapGetters('context', ['loading'])
  },
  methods: {
    ...mapGetters('context', [
      'screenReaderAlert'
    ]),
    ...mapActions('context', [
      'alertScreenReader'
    ])
  }
}
</script>
