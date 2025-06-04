<template>
  <span>
    <a
      :id="`canvas-course-site-${siteId}`"
      :href="`${config.canvasBaseUrl}/courses/${siteId}`"
      target="_blank"
    >
      <span v-if="courseSite">
        {{ courseSite.name }} ({{ courseSite.courseCode }})
      </span>
      <span v-else>
        bCourses site {{ siteId }}
      </span>
      <span class="sr-only">
        (opens in new window)
      </span>
    </a>
    <span
      v-if="kalturaCategory.id"
      :id="`kaltura-category-canvas-${siteId}`"
      class="text-medium-emphasis"
    >
      (Kaltura category {{ kalturaCategory.id }})
    </span>
  </span>
</template>

<script setup>
import {onMounted, ref} from 'vue'
import {getKalturaCategory} from '@/api/kaltura'
import {useContextStore} from '@/stores/context'

const props = defineProps({
  courseSite: {
    type: Object,
    default: null
  },
  siteId: {
    type: Number,
    required: true
  }
})

const {config, currentUser} = useContextStore()

const kalturaCategory = ref({})

onMounted(() => {
  if (currentUser.isAdmin) {
    getKalturaCategory(props.siteId)
      .then(category => {
        kalturaCategory.value = category
      })
  }
})
</script>
