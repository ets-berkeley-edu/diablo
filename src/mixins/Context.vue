<script>
import { mapActions, mapGetters } from 'vuex'

export default {
  name: 'Context',
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
