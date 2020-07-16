<template>
  <div class="d-flex">
    <v-tooltip
      v-if="!isStillTeachingCourse"
      :id="`tooltip-course-${course.sectionId}-instructor-${instructor.uid}-approved`"
      bottom
    >
      <template v-slot:activator="{ on }">
        <v-icon class="pr-1" color="yellow darken-2" v-on="on">mdi-account-remove-outline</v-icon>
      </template>
      {{ instructor.name }} is no longer an instructor of this course.
    </v-tooltip>
    <v-tooltip
      v-if="isEligibleCourse && isStillTeachingCourse && !instructor.approval && !instructor.wasSentInvite"
      :id="`tooltip-course-${course.sectionId}-instructor-${instructor.uid}-not-invited`"
      bottom
    >
      <template v-slot:activator="{ on }">
        <v-icon class="pr-1" color="yellow darken-2" v-on="on">mdi-email-alert-outline</v-icon>
      </template>
      No invite has been sent to {{ instructor.name }}.
    </v-tooltip>
    <v-tooltip
      v-if="isEligibleCourse && isStillTeachingCourse && hasNotApprovedScheduled"
      :id="`tooltip-course-${course.sectionId}-instructor-${instructor.uid}-no-approval`"
      bottom
    >
      <template v-slot:activator="{ on }">
        <v-icon class="pr-1" color="yellow darken-2" v-on="on">mdi-checkbox-blank-outline</v-icon>
      </template>
      {{ instructor.name }} was sent an invite but has not approved the scheduled recordings.
    </v-tooltip>
    <v-tooltip
      v-if="isEligibleCourse && isStillTeachingCourse && instructor.approval"
      :id="`tooltip-course-${course.sectionId}-instructor-${instructor.uid}-approved`"
      bottom
    >
      <template v-slot:activator="{ on }">
        <v-icon class="pr-1" color="green" v-on="on">mdi-check</v-icon>
      </template>
      Approval submitted on {{ instructor.approval.createdAt | moment('MMM D, YYYY') }}.
    </v-tooltip>
    <div>
      <router-link :id="id || `course-${course.sectionId}-instructor-${instructor.uid}`" :to="`/user/${instructor.uid}`">
        {{ instructor.name }}
      </router-link> ({{ instructor.uid }})
    </div>
  </div>
</template>

<script>
  export default {
    name: 'Instructor',
    props: {
      course: {
        required: true,
        type: Object
      },
      id: {
        default: null,
        required: false,
        type: String
      },
      instructor: {
        required: true,
        type: Object
      }
    },
    data: () => ({
      hasNotApprovedScheduled: undefined,
      isEligibleCourse: undefined,
      isStillTeachingCourse: undefined
    }),
    created() {
      const uid = this.instructor.uid
      this.hasNotApprovedScheduled = this.course.scheduled && this.instructor.wasSentInvite && !this.$_.includes(this.course.scheduled.instructorUids, uid)
      this.isEligibleCourse = !!this.course.meetings.eligible.length
      this.isStillTeachingCourse = this.$_.includes(this.$_.map(this.course.instructors, 'uid'), uid)
    }
  }
</script>
