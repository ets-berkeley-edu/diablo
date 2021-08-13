<template>
  <v-dialog v-model="dialog" max-width="360">
    <template #activator="{on, attrs}">
      <v-btn v-bind="attrs" v-on="on">
        Create New<span class="sr-only"> Blackout Date</span>
      </v-btn>
    </template>
    <v-card>
      <v-card-title class="pb-1">
        <h2 class="title">Create New Blackout</h2>
      </v-card-title>
      <v-card-text>
        <span>
          To select a date range, click once on the start date and once on end date.
        </span>
        <div class="pb-4">
          <v-text-field
            id="input-blackout-name"
            v-model="name"
            aria-required="true"
            label="Name"
            maxlength="255"
            :rules="[s => !!s || 'Required', s => !$_.includes(existingNames, $_.trim(s).toLowerCase()) || 'Name not available']"
            @keypress.enter="disableSave ? $_.noop() : create()"
          />
        </div>
        <div class="text-center w-100">
          <c-date-picker
            v-model="range"
            :attributes="attributes"
            :disabled-dates="disabledDates"
            is-range
            :min-date="new Date()"
            :max-date="$moment().add(2, 'years').toDate()"
            title-position="left"
          />
        </div>
      </v-card-text>
      <v-card-actions class="pt-0">
        <v-spacer></v-spacer>
        <div class="pb-3 pr-2">
          <v-btn
            id="save-blackout"
            color="primary"
            :disabled="disableSave"
            @click="create"
          >
            <span v-if="isSaving">
              <v-progress-circular
                class="mr-1"
                :indeterminate="true"
                rotate="5"
                size="18"
                width="2"
              />
              Saving
            </span>
            <span v-if="!isSaving">Save</span>
          </v-btn>
          <v-btn
            id="cancel-edit-of-blackout"
            text
            @click="cancel"
          >
            Cancel
          </v-btn>
        </div>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script>
import Context from '@/mixins/Context'
import {createBlackout} from '@/api/blackout'

export default {
  name: 'CreateBlackoutDialog',
  mixins: [Context],
  props: {
    blackouts: {
      required: true,
      type: Array
    },
    onClose: {
      required: true,
      type: Function
    }
  },
  data: () => ({
    dialog: false,
    isSaving: false,
    name: undefined,
    range: undefined
  }),
  computed: {
    attributes() {
      return this.$_.map(this.blackouts, b => ({
        key: b.name,
        highlight: 'red',
        dates: {
          start: this.$moment(b.startDate).toDate(),
          end: this.$moment(b.endDate).toDate()
        }
      }))
    },
    disabledDates() {
      return this.$_.map(this.blackouts, b => ({
        start: this.$moment(b.startDate).toDate(),
        end: this.$moment(b.endDate).toDate()
      }))
    },
    disableSave() {
      const trimmed = this.$_.trim(this.name)
      return !trimmed || this.$_.includes(this.existingNames, trimmed.toLowerCase()) || !this.range.start || !this.range.end
    },
    existingNames() {
      return this.$_.map(this.blackouts, b => b.name.toLowerCase())
    }
  },
  watch: {
    dialog(isOpen) {
      this.reset()
      if (isOpen) {
        this.$putFocusNextTick('input-blackout-name')
      }
    }
  },
  created() {
    this.reset()
  },
  methods: {
    cancel() {
      this.dialog = false
      this.alertScreenReader('Cancelled.')
      this.onClose(false)
    },
    create() {
      this.isSaving = true
      const format = date => {
        return this.$moment(date).format('YYYY-MM-DD')
      }
      createBlackout(this.name, format(this.range.start), format(this.range.end)).then(() => {
        this.alertScreenReader('Blackout created')
        this.isSaving = false
        this.dialog = false
        this.onClose(true)
      })
    },
    reset() {
      this.name = null
      this.range = {
        start: undefined,
        end: undefined,
      }
    }
  }
}
</script>
