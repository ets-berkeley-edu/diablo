<template>
  <div v-if="!loading">
    <v-card
      max-width="688"
      class="mx-auto"
    >
      <v-img class="white--text align-end" src="@/assets/attic.png">
        <v-card-title>
          <h2 class="display-3">The Attic</h2>
        </v-card-title>
      </v-img>
      <v-card-subtitle class="pb-0">Course Capture</v-card-subtitle>
      <v-card-text class="text--primary">
        <div>University of California, Berkeley</div>
      </v-card-text>
      <v-card-actions>
        <v-btn
          v-for="item in items"
          :key="item.path"
          color="secondary"
          class="ma-2 white--text"
          @click="goToPath('/email/templates')"
        >
          {{ item.title }}
          <v-icon right dark>{{ item.icon }}</v-icon>
        </v-btn>
      </v-card-actions>
    </v-card>
  </div>
</template>

<script>
  import Context from '@/mixins/Context'
  import Utils from '@/mixins/Utils'

  export default {
    name: 'Attic',
    mixins: [Context, Utils],
    data: () => ({
      items: [
        {
          color: 'purple',
          icon: 'mdi-pencil',
          path: '/templates',
          title: 'Email Templates'
        }
      ]
    })
  }
</script>
