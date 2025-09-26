<template>
  <div>
    {{ instructor.name }}<span v-if="currentUser.isAdmin">&nbsp;({{ instructor.uid }})</span>
    <span v-if="instructor.optedInAt" class="text-green">&nbsp;&mdash; Signed up {{ DateTime.fromISO(instructor.optedInAt).toRelativeCalendar({}) }}</span>
    <span v-if="!instructor.optedInAt" class="text-warning">&nbsp;(not yet signed up)</span>
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
