<template>
  <v-tooltip v-if="course.crossListings.length" :id="`course-${course.sectionId}-cross-listings`" bottom>
    <template v-slot:activator="{ on }">
      <v-icon :class="iconClass" v-on="on">
        mdi-format-line-spacing
      </v-icon>
    </template>
    <span v-if="course.crossListings.length === 1">
      <span :id="`course-${course.sectionId}-cross-listing-1`" class="subtitle-2">Cross-listing: {{ course.crossListings[0].label }}</span>
    </span>
    <div v-if="course.crossListings.length !== 1">
      <span class="subtitle-2">Cross-listings:</span>
      <ul>
        <li v-for="(crossListing, index) in course.crossListings" :key="crossListing.sectionId">
          <span :id="`course-${course.sectionId}-cross-listing-${index}`">{{ crossListing.label }}</span>
        </li>
      </ul>
    </div>
  </v-tooltip>
</template>

<script>
  export default {
    name: 'CrossListingTooltip',
    props: {
      course: {
        required: true,
        type: Object
      },
      iconClass: {
        default: '',
        type: String
      }
    }
  }
</script>
