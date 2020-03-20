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
      organizeMySections() {
        const all = []
        const eligibleOnly = []
        this.$_.each(this.$currentUser.teachingSections, s => {
          let course = {
            name: `${s.courseName}, ${s.instructionFormat} ${s.sectionNum}`,
            days: s.meetingDays ? this.$_.join(s.meetingDays, ', ') : undefined,
            instructors: this.oxfordJoin(this.$_.map(s.instructors, 'name')),
            room: s.room,
            sectionId: s.sectionId,
            time: s.meetingStartTime ? `${s.meetingStartTime} - ${s.meetingEndTime}` : undefined,
            title: s.courseTitle
          }
          all.push(course)
          if (s.room.capabilities.length) {
            eligibleOnly.push(course)
          }
        })
        return {
          all,
          eligibleOnly
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
      },
      setPageTitle: phrase => (document.title = `${phrase ? phrase : 'UC Berkeley'} | Course Capture`)
    }
  }
</script>
