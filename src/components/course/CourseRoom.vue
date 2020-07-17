<template>
  <div class="d-flex">
    <v-tooltip
      v-if="!hideEligibility"
      :id="`tooltip-course-${course.sectionId}-room-${room.id}-ineligible`"
      bottom
    >
      <template v-slot:activator="{ on, attrs }">
        <v-icon
          class="pr-1"
          :color="room.capability ? 'light-green' : 'yellow darken-2'"
          v-bind="attrs"
          v-on="on"
        >
          {{ room.capability ? 'mdi-video-plus' : 'mdi-video-off-outline' }}
        </v-icon>
      </template>
      {{ room.location }} is {{ room.capability ? '' : 'not' }} capture-enabled.
    </v-tooltip>
    <v-tooltip
      v-if="!isInRoom(course, room)"
      :id="`tooltip-course-${course.sectionId}-room-${room.id}-obsolete`"
      bottom
    >
      <template v-slot:activator="{ on, attrs }">
        <v-icon
          class="pr-1"
          color="yellow darken-2"
          v-bind="attrs"
          v-on="on"
        >
          mdi-map-marker-remove-outline
        </v-icon>
      </template>
      This course moved out of {{ room.location }}.
    </v-tooltip>
    <div>
      <router-link
        :id="`course-${course.sectionId}-room-${room.id}`"
        :to="`/room/${room.id}`"
      >
        {{ room.location }}
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
        type: Object
      }
    }
  }
</script>
