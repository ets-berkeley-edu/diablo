<template>
  <div class="d-flex">
    <v-tooltip
      v-if="!$_.includes($_.map(course.instructors, 'uid'), instructor.uid)"
      :id="`tooltip-course-${course.sectionId}-instructor-${instructor.uid}-approved`"
      bottom
    >
      <template v-slot:activator="{ on }">
        <v-icon class="pr-1" color="yellow darken-2" v-on="on">mdi-account-remove-outline</v-icon>
      </template>
      {{ instructor.name }} is no longer an instructor of this course.
    </v-tooltip>
    <v-tooltip
      v-if="!instructor.approval && !instructor.wasSentInvite"
      :id="`tooltip-course-${course.sectionId}-instructor-${instructor.uid}-not-invited`"
      bottom
    >
      <template v-slot:activator="{ on }">
        <v-icon class="pr-1" color="yellow darken-2" v-on="on">mdi-email-alert-outline</v-icon>
      </template>
      No invite has been sent to {{ instructor.name }}.
    </v-tooltip>
    <v-tooltip
      v-if="instructor.approval"
      :id="`tooltip-course-${course.sectionId}-instructor-${instructor.uid}-approved`"
      bottom
    >
      <template v-slot:activator="{ on }">
        <v-icon class="pr-1" color="green" v-on="on">mdi-check</v-icon>
      </template>
      Approval submitted on {{ instructor.approval.createdAt | moment('MMM D, YYYY') }}.
    </v-tooltip>
    <div>
      <router-link :id="`course-${course.sectionId}-instructor-${instructor.uid}`" :to="`/user/${instructor.uid}`">
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
      instructor: {
        required: true,
        type: Object
      }
    }
  }
</script>
