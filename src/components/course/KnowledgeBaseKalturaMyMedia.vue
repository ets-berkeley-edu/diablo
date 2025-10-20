<template>
  <div>
    <span class="font-size-18">Please review the following KB articles:</span>
    <ul>
      <li>
        <ExternalLink
          href="https://berkeley.service-now.com/kb/en/what-to-check-while-at-the-classroom-to-ensure-course-capture-is-recording?id=kb_article_view&sysparm_article=KB0014952"
          :icon-size="16"
          link-id="link-publish-my-media"
          text="How to Prevent Recording Issues in the Classroom"
        />
      </li>
      <li>
        <ExternalLink
          href="https://berkeley.service-now.com/kb/en/how-to-share-course-capture-recordings?id=kb_article_view&sysparm_article=KB0014934"
          :icon-size="16"
          link-id="link-embed-rich-content"
          text="How to Share Course Capture Recordings"
        />
      </li>
      <li>
        <ExternalLink
          href="https://berkeley.service-now.com/kb/en/how-do-i-download-kaltura-media?id=kb_article_view&sysparm_article=KB0013825"
          :icon-size="16"
          link-id="link-download-second-stream"
          text="How do I Download Kaltura Media"
        />
      </li>
      <li>
        <ExternalLink
          href="https://rtl.berkeley.edu/services-programs/course-capture/instructor-getting-started-spring-25/course-capture-faq"
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
