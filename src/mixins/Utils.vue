<script>
  import _ from 'lodash'

  export default {
    name: 'Utils',
    methods: {
      getCourseCodes(course) {
        return course.label.split('|').map(l => l.trim())
      },
      getSelectOptionsFromObject(obj, isDisabled=() => false) {
        const options = []
        _.each(obj, (text, value) => options.push({text, value, disabled: isDisabled(value)}))
        return options
      },
      goToPath(path) {
        this.$router.push({ path }, _.noop)
      },
      onNextTick(callable) {
        this.$nextTick(() => {
          let counter = 0
          const job = setInterval(() => (callable() || ++counter > 3) && clearInterval(job), 500)
        })
      },
      oxfordJoin: arr => {
        switch(arr.length) {
          case 1: return _.head(arr)
          case 2: return `${_.head(arr)} and ${_.last(arr)}`
          default: return _.join(_.concat(_.initial(arr), ` and ${_.last(arr)}`), ', ')
        }
      },
      putFocusNextTick(id, cssSelector = null) {
        this.onNextTick(() => {
            let el = document.getElementById(id)
            el = el && cssSelector ? el.querySelector(cssSelector) : el
            el && el.focus()
            return !!el
        })
      },
      stripHtmlAndTrim: html => {
        let text = html && html.replace(/<([^>]+)>/ig,'')
        text = text && text.replace(/&nbsp;/g, '')
        return _.trim(text)
      }
    }
  }
</script>
