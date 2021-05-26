<template>
  <v-form>
    <v-container v-if="!loading" fluid>
      <v-row class="align-start d-flex justify-space-between pb-2" no-gutters>
        <PageTitle icon="mdi-email-edit-outline" :text="pageTitle" />
      </v-row>
      <v-row class="pl-4">
        <v-col cols="8">
          <v-text-field
            id="input-blackout-name"
            v-model="name"
            aria-required="true"
            label="Template Name"
            maxlength="255"
            :rules="[s => !!s || 'Required']"
          >
          </v-text-field>
        </v-col>
        <v-spacer></v-spacer>
      </v-row>
      <v-row class="pl-4">
        <v-col cols="8">
          <v-text-field
            id="input-blackout-start-date"
            v-model="startDate"
            aria-required="true"
            label="Start date"
            maxlength="50"
            :rules="[s => !!s || 'Required']"
          >
          </v-text-field>
        </v-col>
        <v-spacer></v-spacer>
      </v-row>
      <v-row class="pl-4">
        <v-col cols="8">
          <v-text-field
            id="input-blackout-end-date"
            v-model="endDate"
            aria-required="true"
            label="Start date"
            maxlength="50"
            :rules="[s => !!s || 'Required']"
          >
          </v-text-field>
        </v-col>
        <v-spacer></v-spacer>
      </v-row>
      <v-row>
        <v-col cols="8">
          <div class="d-flex">
            <v-btn
              id="save-blackout"
              color="primary"
              :disabled="disableSave"
              @click="createBlackout"
            >
              {{ blackoutId ? 'Save' : 'Create' }}
            </v-btn>
            <v-btn
              id="cancel-edit-of-blackout"
              text
              color="accent"
              @click="cancel"
            >
              Cancel
            </v-btn>
          </div>
        </v-col>
      </v-row>
    </v-container>
  </v-form>
</template>

<script>
import Context from '@/mixins/Context'
import PageTitle from '@/components/util/PageTitle'
import Utils from '@/mixins/Utils'
import {createBlackout, getBlackout, updateBlackout} from '@/api/blackout'

export default {
  name: 'EditBlackout',
  components: {PageTitle},
  mixins: [Context, Utils],
  data: () => ({
    blackoutId: undefined,
    endDate: undefined,
    name: undefined,
    pageTitle: undefined,
    startDate: undefined
  }),
  computed: {
    disableSave() {
      return !this.$_.trim(this.name) || !this.startDate || !this.endDate
    }
  },
  created() {
    this.$loading()
    this.blackoutId = this.$_.get(this.$route, 'params.id')
    if (this.blackoutId) {
      this.pageTitle = 'Create Blackout'
      this.$ready(this.pageTitle)
    } else {
      getBlackout(this.blackoutId).then(data => {
        this.name = data.name
        this.startDate = data.startDate
        this.endDate = data.endDate
        this.pageTitle = `Edit ${this.name}`
        this.$ready(this.pageTitle)
      })
    }
  },
  methods: {
    cancel() {
      this.alertScreenReader('Cancelled.')
      this.$router.push({path: '/blackouts'})
    },
    createBlackout() {
      const done = action => {
        this.alertScreenReader(`Blackout dates ${action}.`)
        this.$router.push({path: '/blackouts'})
      }
      if (this.disableSave) {
        this.reportError('You must fill in the required fields.')
      } else if (this.blackoutId) {
        updateBlackout(this.blackoutId, this.name, this.startDate, this.endDate).then(() => done('updated'))
      } else {
        createBlackout(this.name, this.startDate, this.endDate).then(() => done('created'))
      }
    }
  }
}
</script>
