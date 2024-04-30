<template>
  <div>
    <h4 class="title">Recordings scheduled</h4>
    <v-list v-for="scheduled in course.scheduled" :key="scheduled.kalturaScheduleId">
      <v-list-item-title class="pl-4 pt-3">
        <div v-if="$currentUser.isAdmin" class="d-flex align-bottom">
          <div>
            <a
              id="link-to-edit-kaltura-event"
              :href="`${$config.kalturaMediaSpaceUrl}/recscheduling/index/edit-event/eventid/${scheduled.kalturaScheduleId}`"
              target="_blank"
              aria-label="Open Kaltura MediaSpace in a new window"
            >
              Kaltura series {{ course.scheduled.kalturaScheduleId }} <v-icon small class="pb-1">mdi-open-in-new</v-icon>
            </a>
          </div>
        </div>
      </v-list-item-title>
      <v-list-item two-line>
        <v-list-item-content>
          <v-list-item-title>Scheduled on</v-list-item-title>
          <v-list-item-subtitle>{{ scheduled.createdAt | moment('MMM DD, YYYY') }}</v-list-item-subtitle>
        </v-list-item-content>
        <v-list-item-content>
          <v-list-item-title>Recording Type</v-list-item-title>
          <v-list-item-subtitle>{{ scheduled.recordingTypeName }}</v-list-item-subtitle>
        </v-list-item-content>
      </v-list-item>
      <v-list-item two-line>
        <v-list-item-content>
          <v-list-item-title>Publish Type</v-list-item-title>
          <v-list-item-subtitle>{{ scheduled.publishTypeName }}</v-list-item-subtitle>
        </v-list-item-content>
        <v-list-item-content>
          <v-list-item-title>Admin Proxy Publish</v-list-item-title>
          <v-list-item-subtitle id="admin-proxy-status">
            {{ course.canAprxInstructorsEditRecordings ? 'Yes' : 'No' }}
          </v-list-item-subtitle>
        </v-list-item-content>
      </v-list-item>
      <v-list-item v-if="$currentUser.isAdmin && adminAlerts.length" two-line class="pb-3">
        <v-list-item-content>
          <v-list-item-title>
            <v-icon class="pb-1 pr-1" color="red">mdi-alert</v-icon>
            {{ $_.capitalize(oxfordJoin(adminAlerts).toLowerCase()) }}
          </v-list-item-title>
        </v-list-item-content>
      </v-list-item>
      <v-card-text v-if="currentUserMustApprove">
        <v-container>
          <v-row class="pb-4">
            <h4 class="ml-3 title">We need your approval</h4>
          </v-row>
          <v-row no-gutters align="start">
            <v-col md="auto">
              <v-checkbox id="agree-to-terms-checkbox" v-model="agreedToTerms" class="mt-0" />
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
    </v-list>
  </div>
</template>

<script>
import Context from '@/mixins/Context'
import TermsAgreementText from '@/components/util/TermsAgreementText'
import Utils from '@/mixins/Utils'
import {approve} from '@/api/course'

export default {
  name: 'ScheduledCourse',
  components: {TermsAgreementText},
  mixins: [Context, Utils],
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
    adminAlerts: undefined,
    agreedToTerms: false,
    currentUserMustApprove: undefined,
    isApproving: false
  }),
  created() {
    const alertKeys = this.$_.filter(this.course.scheduled.alerts, alert => alert.includes('admin'))
    this.adminAlerts = this.$_.map(alertKeys, key => this.$config.emailTemplateTypes[key].replace('Admin alert: ', ''))
    this.currentUserMustApprove = !this.course.deletedAt
      && !this.$currentUser.isAdmin
      && !this.$_.includes(this.$_.map(this.course.approvals, 'approvedBy'), this.$currentUser.uid)
  },
  methods: {
    approve() {
      this.isApproving = true
      approve(
        this.course.scheduled.publishType,
        this.course.scheduled.recordingType,
        this.course.sectionId
      ).then(data => {
        this.isApproving = this.currentUserMustApprove = false
        this.afterApprove(data)
        this.alertScreenReader('Approval received.')
      })
    }
  }
}
</script>
