<template>
  <div>
    <h1 id="page-title" tabindex="-1">
      <div class="d-flex align-center" :class="classForH1">
        <v-icon
          v-if="is420"
          aria-label="Play entertaining video clip (opens in new tab)"
          class="mr-3"
          :color="theme.global.current.dark ? 'white' : 'primary'"
          :href="contextStore.config.easterEgg420"
          :icon="mdiWeatherTornado"
          size="36"
          tag="a"
          target="_blank"
        />
        <v-icon
          v-if="!is420"
          class="mr-3"
          :color="theme.global.current.dark ? 'white' : 'primary'"
          :icon="icon"
          size="36"
        />
        <span :class="clazz()" tabindex="-1"> {{ text }}</span>
      </div>
    </h1>
    <div v-if="subTitle" class="ml-5 pl-8 text-subtitle-1 text-primary">
      {{ subTitle }}
    </div>
  </div>
</template>

<script setup>
import {DateTime} from 'luxon'
import {mdiWeatherTornado} from '@mdi/js'
import {onMounted, ref} from 'vue'
import {useTheme} from 'vuetify'
import {useContextStore} from '@/stores/context'

const props = defineProps({
  classForH1: {
    default: undefined,
    required: false,
    type: String
  },
  icon: {
    required: true,
    type: String
  },
  subTitle: {
    default: undefined,
    required: false,
    type: String
  },
  text: {
    required: true,
    type: String
  }
})

const contextStore = useContextStore()
const is420 = ref(false)
const theme = useTheme()

onMounted(() => {
  is420.value = DateTime.now().toFormat('H:mm') === '16:20'
})

const clazz = () => {
  return props.text.length > 40 ? `${props.classForH1} text-h4` : props.classForH1
}
</script>
