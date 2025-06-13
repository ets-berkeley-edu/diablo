<template>
  <span>
    <ExternalLink
      :href="`${config.canvasBaseUrl}/courses/${siteId}`"
      :icon-size="16"
      :link-id="`canvas-course-site-${siteId}`"
    >
      <span v-if="courseSite">{{ courseSite.name }} ({{ courseSite.courseCode }})</span>
      <span v-else>bCourses site {{ siteId }}</span>
    </ExternalLink>
    <span
      v-if="kalturaCategory.id"
      :id="`kaltura-category-canvas-${siteId}`"
      class="text-medium-emphasis text-body-2"
    >
      (Kaltura category {{ kalturaCategory.id }})
    </span>
  </span>
</template>

<script setup>
import {onMounted, ref} from 'vue'
import ExternalLink from '@/components/util/ExternalLink'
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
