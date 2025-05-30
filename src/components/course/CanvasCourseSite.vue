<template>
  <span>
    <a
      :id="`canvas-course-site-${siteId}`"
      aria-label="Open Canvas course site in a new window"
      :href="`${config.canvasBaseUrl}/courses/${siteId}`"
      target="_blank"
    >
      <span v-if="courseSite">
        {{ courseSite.name }} ({{ courseSite.courseCode }})
      </span>
      <span v-else>
        bCourses site {{ siteId }}
      </span>
    </a>
    <span
      v-if="kalturaCategory"
      :id="`kaltura-category-canvas-${siteId}`"
      class="font-weight-light"
    >
      (Kaltura category {{ kalturaCategory.id }})
    </span>
  </span>
</template>

<script setup>
import {ref, onMounted} from 'vue'
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
