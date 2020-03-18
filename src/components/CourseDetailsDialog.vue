<template>
  <div class="text-center">
    <v-dialog
      v-model="dialog"
      width="50%"
    >
      <template v-slot:activator="{ on }">
        <v-btn
          color="primary"
          text
          v-on="on"
        >
          {{ course.courseName }}
        </v-btn>
      </template>

      <v-card>
        <v-card-title
          class="headline  lighten-2"
          primary-title
        >
          <h3>{{ course.courseName }}</h3>
        </v-card-title>

        <v-card-text>
          <h4>{{ course.courseTitle }}</h4>
          <div v-for="approval in course.approvals" :key="approval.approvedByUid">
            <ul>
              <li>Approved by {{ approval.approvedByUid }}</li>
              <li>Publish type: {{ approval.publishTypeName }}</li>
              <li>Recording type {{ approval.recordingTypeName }}</li>
            </ul>
          </div>
        </v-card-text>

        <v-divider></v-divider>

        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn
            color="primary"
            text
            @click="close"
          >
            Close
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script>
  export default {
    name: 'CourseDetailsDialog',
    props: {
      course: {
        required: true,
        type: Object
      }
    },
    data: () => ({
      dialog: false
    }),
    methods: {
      close() {
        this.dialog = false
      }
    }
  }
</script>
