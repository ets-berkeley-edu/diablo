<template>
  <v-card tile>
    <v-list-item-title class="pl-4 pt-4">
      <h4 class="title">Recordings scheduled</h4>
      <div v-if="$currentUser.isAdmin" class="d-flex align-bottom">
        <div>
          <a
            id="link-to-edit-kaltura-event"
            :href="`${$config.kalturaMediaSpaceUrl}/recscheduling/index/edit-event/eventid/${course.scheduled.kalturaScheduleId}`"
            target="_blank"
            aria-label="Open Kaltura MediaSpace in a new window"
          >
            Kaltura series {{ course.scheduled.kalturaScheduleId }} <v-icon small class="pb-1">mdi-open-in-new</v-icon>
          </a>
        </div>
      </div>
    </v-list-item-title>
    <v-list-item two-line class="pb-3">
      <v-list-item-content>
        <v-list-item-title>Scheduled on</v-list-item-title>
        <v-list-item-subtitle>{{ course.scheduled.createdAt | moment('MMM DD, YYYY') }}</v-list-item-subtitle>
      </v-list-item-content>
      <v-list-item-content>
        <v-list-item-title>Recording Type</v-list-item-title>
        <v-list-item-subtitle>{{ course.scheduled.recordingTypeName }}</v-list-item-subtitle>
      </v-list-item-content>
      <v-list-item-content>
        <v-list-item-title>Publish Type</v-list-item-title>
        <v-list-item-subtitle>{{ course.scheduled.publishTypeName }}</v-list-item-subtitle>
      </v-list-item-content>
    </v-list-item>
    <v-list-item v-if="$currentUser.isAdmin && course.scheduled.alerts.length" two-line class="pb-3">
      <v-list-item-content>
        <v-list-item-title>
          <v-icon class="pb-1 pr-1" color="red">mdi-alert</v-icon>
          <OxfordJoin v-slot="{ item }" :items="course.scheduled.alerts">
            {{ $config.emailTemplateTypes[item] }}
          </OxfordJoin>
        </v-list-item-title>
      </v-list-item-content>
    </v-list-item>
    <v-card-text v-if="currentUserMustApprove">
      <v-container>
        <v-row class="pb-2">
          <h4 class="title">We need your approval</h4>
        </v-row>
        <v-row no-gutters align="start">
          <v-col md="auto">
            <v-checkbox id="agree-to-terms-checkbox" v-model="agreedToTerms" class="mt-0"></v-checkbox>
          </v-col>
          <v-col>
            <TermsAgreementText />
          </v-col>
        </v-row>
        <v-row lg="2">
          <v-col>
            <v-btn
              id="btn-approve"
              class="float-right"
              color="success"
              :disabled="!agreedToTerms || isApproving"
              @click="approve"
            >
              <v-progress-circular
                v-if="isApproving"
                class="mr-2"
                color="primary"
                indeterminate
                size="18"
                width="3"
              ></v-progress-circular>
              {{ isApproving ? 'Approving' : 'Approve' }}
            </v-btn>
          </v-col>
        </v-row>
      </v-container>
    </v-card-text>
  </v-card>
</template>

<script>
  import Context from '@/mixins/Context'
  import OxfordJoin from '@/components/util/OxfordJoin'
  import TermsAgreementText from '@/components/util/TermsAgreementText'
  import {approve} from '@/api/course'

  export default {
    name: 'ScheduledCourse',
    components: {OxfordJoin, TermsAgreementText},
    mixins: [Context],
    props: {
      afterApprove: {
        required: true,
        type: Function
      },
      course: {
        required: true,
        type: Object
      }
    },
    data: () => ({
      agreedToTerms: false,
      currentUserMustApprove: undefined,
      isApproving: false
    }),
    created() {
      this.currentUserMustApprove = !this.$currentUser.isAdmin && !this.$_.includes(this.$_.map(this.course.approvals, 'approvedBy.uid'), this.$currentUser.uid)
    },
    methods: {
      approve() {
        this.isApproving = true
        approve(this.course.scheduled.publishType, this.course.scheduled.recordingType, this.course.sectionId).then(data => {
          this.isApproving = this.currentUserMustApprove = false
          this.afterApprove(data)
          this.alertScreenReader('Approval received.')
        })
      }
    }
  }
</script>
