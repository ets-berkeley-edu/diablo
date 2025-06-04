<template>
  <div class="d-flex flex-column flex-grow-1">
    <label
      :id="`${props.idPrefix}-label`"
      :for="`${props.idPrefix}-input`"
      :class="props.labelClass"
      class="mb-1"
    >
      <span v-if="props.label">{{ props.label }}</span>
      <span v-if="props.placeholder" class="sr-only">
        {{ props.placeholder }}
      </span>
    </label>
    <div class="d-flex align-center">
      <AccessibleCombobox
        aria-description="Collaborator U I D or email lookup. Expect auto suggest."
        autocomplete="off"
        color="primary"
        density="compact"
        :disabled="disabled"
        :filter-results="executeSearch"
        :get-value="() => selected"
        :id-prefix="idPrefix"
        is-autocomplete
        :is-busy="isSearching"
        :is-invalid="!!props.errorMessage"
        :items="formattedItems"
        :label="label"
        :list-label="listLabel"
        :on-clear="clearErrors"
        :placeholder="placeholder"
        :set-value="v => selected = v"
        :when-item-selected="onSelectResult"
      />
      <slot name="append" />
    </div>
    <div aria-live="assertive" role="alert">
      <div
        v-if="props.errorMessage"
        :id="`${props.idPrefix}-error`"
        class="text-error px-3 mt-1"
      >
        {{ props.errorMessage }}
      </div>
    </div>
  </div>
</template>

<script setup>
import {computed, ref} from 'vue'
import {debounce, get, join, split, trim} from 'lodash'
import {searchUsers} from '@/api/user'
import AccessibleCombobox from '@/components/util/AccessibleCombobox'

const props = defineProps({
  clearErrors: {
    required: true,
    type: Function
  },
  disabled: {
    required: true,
    type: Boolean
  },
  errorMessage: {
    default: '',
    required: false,
    type: String
  },
  idPrefix: {
    default: 'person-lookup',
    required: false,
    type: String
  },
  label: {
    required: true,
    type: String
  },
  listLabel: {
    type: String,
    required: true
  },
  onSelectResult: {
    default: () => {},
    type: Function
  },
  placeholder: {
    default: 'UID or email',
    type: String,
    required: false
  }
})

const isSearching = ref(false)
const searchTokenMatcher= ref()
const selected = ref()
const suggestions = ref([])

defineExpose({selected})

const formattedItems = computed(() =>
  suggestions.value.map(user => {
    let title = trim(`${get(user, 'firstName', '')} ${get(user, 'lastName', '')}`)
    if (user.email) {
      title += ` (${user.email})`
    }
    if (user.uid) {
      title += ` (${user.uid})`
    }
    return {
      title: title,
      raw: user
    }
  })
)

const executeSearch = debounce(snippet => {
  if (snippet) {
    isSearching.value = true
    searchUsers(snippet).then(results => {
      const tokens = split(trim(snippet), /\W/g)
      searchTokenMatcher.value = RegExp(join(tokens, '|'), 'gi')
      suggestions.value = results
      isSearching.value = false
    })
  } else {
    suggestions.value = []
  }
}, 500)
</script>
