<template>
  <div class="d-flex">
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
  }
}
</script>
