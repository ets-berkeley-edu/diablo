<script>
  import _ from 'lodash'

  export default {
    name: 'Utils',
    methods: {
      oxfordJoin: arr => {
        switch(arr.length) {
          case 1: return _.head(arr)
          case 2: return `${_.head(arr)} and ${_.last(arr)}`
          default: return _.join(_.concat(_.initial(arr), ` and ${_.last(arr)}`), ', ')
        }
      },
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
