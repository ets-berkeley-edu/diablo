<script>
  export default {
    name: 'DomUtils',
    methods: {
      putFocusNextTick(id, cssSelector = null) {
        this.$nextTick(() => {
          let counter = 0
          const putFocus = setInterval(() => {
            let el = document.getElementById(id)
            el = el && cssSelector ? el.querySelector(cssSelector) : el
            el && el.focus()
            if (el || ++counter > 3) {
              // Abort after success or three attempts
              clearInterval(putFocus)
            }
          }, 500)
        })
      }
    }
  }
</script>
