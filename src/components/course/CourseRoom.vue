<template>
  <div class="d-flex">
    <v-tooltip
      v-if="!hideEligibility"
      :id="`tooltip-course-${course.sectionId}-room-${roomId}-ineligible`"
      bottom
    >
      <template #activator="{on, attrs}">
        <v-icon
          class="pr-1"
          :color="capability ? 'light-green' : 'yellow darken-2'"
          v-bind="attrs"
          v-on="on"
        >
          {{ capability ? 'mdi-video-plus' : 'mdi-video-off-outline' }}
        </v-icon>
      </template>
      <span v-if="location">{{ location }} is {{ capability ? '' : 'not' }} capture-enabled.</span>
      <span v-if="!location">No meeting location.</span>
    </v-tooltip>
    <v-tooltip
      v-if="!isInRoom(course, room)"
      :id="`tooltip-course-${course.sectionId}-room-${roomId}-obsolete`"
      bottom
    >
      <template #activator="{on, attrs}">
        <v-icon
          class="pr-1"
          color="yellow darken-2"
          v-bind="attrs"
          v-on="on"
        >
          mdi-map-marker-remove-outline
        </v-icon>
      </template>
      <span v-if="location">This course moved out of {{ location }}.</span>
      <span v-if="!location">No meeting location.</span>
    </v-tooltip>
    <div v-if="roomId">
      <router-link
        :id="`course-${course.sectionId}-room-${roomId}`"
        :to="`/room/${roomId}`"
      >
        {{ location }}
      </router-link>
    </div>
  </div>
</template>

<script>
import Utils from '@/mixins/Utils'

export default {
  name: 'CourseRoom',
  mixins: [Utils],
  props: {
    course: {
      required: true,
      type: Object
    },
    hideEligibility: {
      type: Boolean
    },
    room: {
      required: true,
      validator: prop => prop || prop === null
    }
  },
  data: () => ({
    capability: undefined,
    location: undefined,
    roomId: undefined
  }),
  created() {
    this.capability = this.$_.get(this.room, 'capability')
    this.location = this.$_.get(this.room, 'location')
    this.roomId = this.$_.get(this.room, 'id')
  }
}
</script>
