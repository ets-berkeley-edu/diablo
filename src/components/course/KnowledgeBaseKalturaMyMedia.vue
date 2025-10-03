<template>
  <div>
    <span class="font-size-18">Based on the selected Recording Placement, please review the following KB articles.</span>
    <ul>
      <li>
        <ExternalLink
          href="https://berkeley.service-now.com/kb?id=kb_article_view&sysparm_article=KB0013882"
          :icon-size="16"
          link-id="link-publish-my-media"
          text="How to Publish from My Media"
        />
      </li>
      <li>
        <ExternalLink
          href="https://berkeley.service-now.com/kb?id=kb_article_view&sysparm_article=KB0013623"
          :icon-size="16"
          link-id="link-embed-rich-content"
          text="How to Embed in bCourses using the Rich Content Editor"
        />
      </li>
      <li>
        <ExternalLink
          href="https://berkeley.service-now.com/kb?id=kb_article_view&sysparm_article=KB0014115"
          :icon-size="16"
          link-id="link-download-second-stream"
          text="How to Download the Second Stream of the Recording"
        />
      </li>
      <li>
        <ExternalLink
          href="https://rtl.berkeley.edu/services-programs/course-capture/instructors-getting-started/course-capture-faq"
          :icon-size="16"
          link-id="link-faq"
          text="Course Capture FAQ"
        />
      </li>
    </ul>
  </div>
</template>

<script setup lang="ts">
import ExternalLink from '@/components/util/ExternalLink.vue'
</script>
