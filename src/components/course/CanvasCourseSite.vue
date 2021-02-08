<template>
  <div>
    <a
      :id="`canvas-course-site-${site.courseSiteId}`"
      aria-label="Open Canvas course site in a new window"
      :href="`${$config.canvasBaseUrl}/courses/${site.courseSiteId}`"
      target="_blank"
    >{{ site.courseSiteName }}</a>
    <span v-if="kalturaCategory" :id="`kaltura-category-canvas-${site.courseSiteId}`" class="font-weight-light">
      (Kaltura category {{ kalturaCategory.id }})
    </span>
  </div>
</template>

<script>
import {getKalturaCategory} from '@/api/kaltura'

export default {
  name: 'CanvasCourseSite',
  props: {
    site: {
      required: true,
      type: Object
    }
  },
  data: () => ({
    kalturaCategory: undefined
  }),
  mounted() {
    if (this.$currentUser.isAdmin) {
      getKalturaCategory(this.site.courseSiteId).then(category => {
        this.kalturaCategory = category
      })
    }
  }
}
</script>
