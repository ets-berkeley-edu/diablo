<template>
  <span>
    <a
      :id="`canvas-course-site-${siteId}`"
      aria-label="Open Canvas course site in a new window"
      :href="`${$config.canvasBaseUrl}/courses/${siteId}`"
      target="_blank"
    >
      <span v-if="courseSite">{{ courseSite.name }} ({{ courseSite.courseCode }})</span>
      <span v-if="!courseSite">bCourses site {{ siteId }}</span>
    </a>
    <span v-if="kalturaCategory" :id="`kaltura-category-canvas-${siteId}`" class="font-weight-light">
      (Kaltura category {{ kalturaCategory.id }})
    </span>
  </span>
</template>

<script>
import {getKalturaCategory} from '@/api/kaltura'

export default {
  name: 'CanvasCourseSite',
  props: {
    courseSite: {
      default: () => {},
      required: false,
      type: Object
    },
    siteId: {
      required: true,
      type: Number
    }
  },
  data: () => ({
    kalturaCategory: undefined
  }),
  mounted() {
    if (this.$currentUser.isAdmin) {
      getKalturaCategory(this.siteId).then(category => {
        this.kalturaCategory = category
      })
    }
  }
}
</script>
