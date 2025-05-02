<script>
import _ from 'lodash'

export default {
  name: 'Utils',
  methods: {
    decamelize: (str, separator=' ') => _.capitalize(str.replace(/([a-z\d])([A-Z])/g, '$1' + separator + '$2').replace(/([A-Z]+)([A-Z][a-z\d]+)/g, '$1' + separator + '$2')),
    getCourseCodes(course) {
      return course.label.split('|').map(l => l.trim())
    },
    getDisplayMeetings(course) {
      if (course.meetings.eligible.length) {
        return course.meetings.eligible
      } else {
        return course.meetings.ineligible
      }
    },
    getSelectOptionsFromObject(obj, isDisabled=() => false) {
      const options = []
      _.each(obj, (text, value) => options.push({text, value, disabled: isDisabled(value)}))
      return options
    },
    getTermName: termId => {
      const id = termId.toString()
      let termName = null
      if (id.length === 4) {
        const seasons = {'0': 'Winter', '2': 'Spring', '5': 'Summer', '8': 'Fall'}
        termName = `${seasons[id.slice(3, 4)]} ${_.startsWith(id, '1') ? '19' : '20'}${id.slice(1, 3)}`
      }
      return termName
    },
    goToPath(path) {
      this.$router.push({path}, _.noop)
    },
    isInRoom(course, room) {
      const meetings = course.meetings.eligible.concat(course.meetings.ineligible)
      return room && _.includes(_.map(meetings, 'room.id'), room.id)
    },
    oxfordJoin: arr => {
      switch(arr.length) {
      case 1: return _.head(arr)
      case 2: return `${_.head(arr)} and ${_.last(arr)}`
      default: return _.join(_.concat(_.initial(arr), ` and ${_.last(arr)}`), ', ')
      }
    },
    partitionCoursesByEligibility(courses, eligibleCourses, ineligibleCourses) {
      _.each(courses, c => {
        if (c.meetings.eligible.length) {
          eligibleCourses.push(c)
          if (c.meetings.ineligible.length) {
            const courseCopyWithIneligibleMeetings = _.cloneDeep(c)
            courseCopyWithIneligibleMeetings.meetings.eligible = []
            courseCopyWithIneligibleMeetings.scheduled = null
            ineligibleCourses.push(courseCopyWithIneligibleMeetings)
          }
        } else {
          ineligibleCourses.push(c)
        }
      })
    },
    stripAnchorRef: path => _.split(path, '#', 1)[0],
    stripHtmlAndTrim: html => {
      let text = html && html.replace(/<([^>]+)>/ig,'')
      text = text && text.replace(/&nbsp;/g, '')
      return _.trim(text)
    }
  }
}
</script>
