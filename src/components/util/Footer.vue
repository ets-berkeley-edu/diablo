<template>
  <v-footer color="transparent" fixed>
    <v-container fluid>
      <v-row no-gutters>
        <v-col>
          <v-card
            class="black--text pa-2"
            outlined
            tile>
            <img alt="UC Berkeley logo" src="@/assets/uc-berkeley-logo.svg" />
          </v-card>
        </v-col>
        <v-col class="font-weight-light" offset-md="4">
          <v-card
            class="black--text pa-2 subtitle-2 text--disabled"
            outlined
            tile>
            <div class="text-no-wrap">
              Problem? Question? Email us at {{ $config.supportEmailAddress }}
            </div>
            <div>
              <v-icon small color="grey">mdi-copyright</v-icon> {{ new Date().getFullYear() }}
              The Regents of the University of California
            </div>
          </v-card>
        </v-col>
      </v-row>
    </v-container>
  </v-footer>
</template>

<script>
  export default {
    name: 'Footer'
  }
</script>
