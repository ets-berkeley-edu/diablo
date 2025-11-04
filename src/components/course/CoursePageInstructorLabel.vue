<template>
  <div class="d-flex align-center flex-wrap gap-2 instructor-label">
    <span>
      {{ instructor.name }}<span v-if="currentUser.isAdmin">&nbsp;({{ instructor.uid }})</span>
      <span v-if="instructor.optedInAt">&nbsp;opted in {{ DateTime.fromISO(instructor.optedInAt).toRelativeCalendar({}) }}.</span>
      <span v-if="!instructor.optedInAt">&nbsp;has NOT yet opted in.</span>
    </span>
  </div>
</template>

<script setup lang="ts">
import type {PropType} from 'vue'
import {DateTime} from 'luxon'
import type {CourseInstructor} from '@/lib/types'
import {useContextStore} from '@/stores/context'

defineProps({
  instructor: {
    required: true,
    type: Object as PropType<CourseInstructor>
  }
})

const currentUser = useContextStore().currentUser
</script>

<style scoped>
.instructor-label {
  font-size: 18px;
}
</style>
