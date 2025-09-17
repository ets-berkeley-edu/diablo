<template>
  <div>
    Based on the selected Recording Placement, please review the following KB articles.
    <ul>
      <li>
        <ExternalLink
          href="https://berkeley.service-now.com/kb?id=kb_article_view&sysparm_article=KB0014032"
          :icon-size="16"
          link-id="link-remove-recording"
          text="How to Remove a Recording from the Media Gallery"
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
