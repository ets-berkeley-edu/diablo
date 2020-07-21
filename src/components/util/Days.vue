<template>
  <span>
    <span class="sr-only">Days of the week:</span>
    <span v-for="(day, index) in namesOfDays" :key="index">
      <abbr :title="day">{{ day.slice(0, 2).toUpperCase() }}</abbr><span v-if="showComma(namesOfDays, index)" :class="{'pr-1': omitComma}"><span :class="{'sr-only': omitComma}">, </span></span>
    </span>
  </span>
</template>

<script>
  export default {
    name: 'Days',
    props: {
      namesOfDays: {
        required: true,
        type: Array
      },
      omitComma: {
        type: Boolean
      }
    },
    methods: {
      showComma: (list, index) => list.length > 1 && index < list.length - 1
    }
  }
</script>
