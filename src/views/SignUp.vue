<template>
  <div>
    <v-container fluid>
      <v-row class="pl-3">
        <h1>{{ pageTitle }}</h1>
      </v-row>
      <v-row class="pl-3">
        <h2>{{ section.courseTitle }}</h2>
      </v-row>
      <v-row>
        <v-col lg="3" md="3" sm="3">
          <v-card class="mb-3 mr-3 mt-3 pa-6" outlined tile>
            <v-row>
              <v-col md="auto">
                <v-icon>mdi-school-outline</v-icon>
              </v-col>
              <v-col>
                {{ oxfordJoin($_.map(section.instructors, 'name')) }}
              </v-col>
            </v-row>
            <v-row v-if="section.meetingDays">
              <v-col md="auto">
                <v-icon>mdi-calendar</v-icon>
              </v-col>
              <v-col>
                {{ $_.join(section.meetingDays, ', ') }}
              </v-col>
            </v-row>
            <v-row v-if="section.meetingStartTime">
              <v-col md="auto">
                <v-icon>mdi-clock-outline</v-icon>
              </v-col>
              <v-col>
                {{ section.meetingStartTime }} - {{ section.meetingEndTime }}
              </v-col>
            </v-row>
            <v-row>
              <v-col md="auto">
                <v-icon>mdi-map-marker</v-icon>
              </v-col>
              <v-col>
                {{ section.meetingLocation }}
              </v-col>
            </v-row>
          </v-card>
        </v-col>
        <v-col lg="9" md="9" sm="9">
          <v-card
            class="ma-3 pa-6"
            outlined
            tile
          >
            {{ section }}
          </v-card>
        </v-col>
      </v-row>
    </v-container>
  </div>
</template>

<script>
  import Utils from '@/mixins/Utils'

  export default {
    name: 'SignUp',
    mixins: [Utils],
    data: () => ({
      section: undefined,
      pageTitle: undefined

    }),
    created() {
      const termId = this.$_.get(this.$route, 'params.termId')
      const sectionId = this.$_.get(this.$route, 'params.sectionId')
      this.section = this.$_.find(this.$currentUser.teachingSections, s => s['sectionId'] === sectionId && s['termId'] === termId)
      this.pageTitle = `${this.section.courseName } ${this.section.sectionNum} - ${this.section.instructionFormat} ${this.section.sectionNum}`
      this.setPageTitle(this.pageTitle)
    }
  }
</script>
