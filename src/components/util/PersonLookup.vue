<template>
  <div class="d-flex flex-column flex-grow-1">
    <div :class="{'col col-4': props.inline}">
      <label
        :id="`${props.id}-label`"
        :for="props.id"
        :class="props.labelClass"
      >
        <span v-if="props.label">{{ props.label }}</span>
        <span v-if="props.placeholder" class="sr-only">
          {{ props.placeholder }}
        </span>
      </label>
    </div>
    <div :class="{ 'col col-6': props.inline, 'pt-1': !props.inline }">
      <AccessibleCombobox
        aria-description="Collaborator U I D or email lookup. Expect auto suggest."
        autocomplete="off"
        :clazz="{'mt-1 text-black': true}"
        :clearable="!isSearching"
        color="primary"
        density="compact"
        :disabled="disabled"
        :filter-results="executeSearch"
        :get-value="() => get(selected, 'label')"
        :id-prefix="idPrefix"
        is-autocomplete
        :is-busy="isSearching"
        :items="formattedItems"
        item-title="title"
        :label="label"
        :list-label="listLabel"
        :maxlength="56"
        min-width="12rem"
        :on-clear="onClearSearch"
        :placeholder="placeholder"
        :set-value="s => selected = s.raw"
      />
    </div>

    <div aria-live="assertive" :class="{'col col-2 pl-0': props.inline }" role="alert">
      <div
        v-if="props.errorMessage"
        :id="`${props.id}-error`"
        class="v-messages text-error px-3 mt-1"
      >
        {{ props.errorMessage }}
      </div>
    </div>
  </div>
</template>

<script setup>
import {ref, computed, watch} from 'vue'
import debounce from 'lodash/debounce'
import split from 'lodash/split'
import trim from 'lodash/trim'
import join from 'lodash/join'
import {searchUsers} from '@/api/user'
import AccessibleCombobox from '@/components/util/AccessibleCombobox'
import {get} from 'lodash'

const props = defineProps({
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
const search = ref(null)
const searchTokenMatcher= ref(null)
const selected = ref(null)
const suggestions = ref([])

const formattedItems = computed(() =>
  suggestions.value.map(user => ({
    title: `${user.firstName} ${user.lastName} (${user.email}) (${user.uid})`,
    raw: user
  }))
)

// perform actual API search
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
    isSearching.value = false
    searchTokenMatcher.value = null
    selected.value = null
    suggestions.value = []
  }
}, 500)

const onClearSearch = () => {
  suggestions.value = []
  isSearching.value = false
}

watch(selected, suggestion => {
  if (!suggestion) {
    search.value = null
  }
  props.onSelectResult(suggestion)
})
</script>
