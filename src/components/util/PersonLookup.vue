<template>
  <div :class="containerClass">
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
      <v-autocomplete
        :id="props.id"
        ref="autocomplete"
        v-model="selected"
        v-model:search-input="search"
        :allow-overflow="false"
        :append-icon="null"
        :aria-disabled="props.disabled"
        :aria-label="toLabel(selected)"
        auto-select-first
        background-color="white"
        class="person-lookup"
        :class="props.inputClass"
        dense
        :disabled="props.disabled"
        :error="!!props.errorMessage"
        :error-messages="props.errorMessage ? [props.errorMessage] : []"
        hide-details
        :hide-no-data="isSearching || !search"
        :items="suggestions"
        light
        :loading="isSearching ? 'tertiary' : false"
        :menu-props="menuProps"
        no-data-text="No results found."
        no-filter
        outlined
        :placeholder="props.placeholder"
        return-object
        single-line
        @blur="onBlur"
        @focus="onFocus"
        @update:list-index="onHighlight"
      >
        <template #selection="{ item }">
          <span class="text-nowrap">{{ toLabel(item) }}</span>
        </template>
        <template #item="{ item, attrs, on }">
          <v-list-item
            v-bind="attrs"
            :aria-selected="item === highlightedItem"
            class="tertiary--text"
            v-on="on"
          >
            <span v-html="suggest(item)" />
          </v-list-item>
        </template>
      </v-autocomplete>
    </div>

    <div :class="{ 'col col-2 pl-0': props.inline }">
      <div
        v-if="props.errorMessage"
        :id="`${props.id}-error`"
        class="v-messages error--text px-3 mt-1"
        :class="theme.global.current.value.dark ? 'text--lighten-2' : ''"
        role="alert"
      >
        {{ props.errorMessage }}
      </div>
    </div>
  </div>
</template>

<script setup>
import {
  defineProps,
  ref,
  reactive,
  computed,
  watch,
  nextTick,
  onMounted,
  onBeforeUnmount,
} from 'vue'
import debounce from 'lodash/debounce'
import split from 'lodash/split'
import trim from 'lodash/trim'
import join from 'lodash/join'
import {searchUsers} from '@/api/user'
import {useTheme} from 'vuetify'

// declare props
const props = defineProps({
  disabled: Boolean,
  errorMessage: {
    type: String,
    default: null
  },
  id: {
    type: String,
    default: 'input-person-lookup-autocomplete'
  },
  inline: {
    type: Boolean,
    default: null
  },
  inputClass: {
    type: String,
    default: null
  },
  label: {
    type: String,
    default: null
  },
  labelClass: {
    type: String,
    default: null
  },
  menuLabel: {
    type: String,
    required: true
  },
  onSelectResult: {
    type: Function,
    default: () => {}
  },
  placeholder: {
    type: String, default: 'Name or UID'
  }
})

// theme for light/dark
const theme = useTheme()

// refs & reactive state
const autocomplete = ref(null)
const highlightedItem = ref(null)
const isSearching = ref(false)
const menuObserver = ref(null)
const menuProps = reactive({ contentClass: 'v-sheet--outlined autocomplete-menu' })
const search = ref(null)
const searchTokenMatcher= ref(null)
const selected = ref(null)
const suggestions = ref([])

// container class
const containerClass = computed(() =>
  props.inline
    ? 'row d-flex align-center row--dense'
    : 'd-flex flex-column flex-grow-1'
)

// perform actual API search
function executeSearch(snippet) {
  if (snippet) {
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
}

// debounce it
const debouncedSearch = debounce(executeSearch, 300)

// watch the search input
watch(search, snippet => {
  isSearching.value = true
  debouncedSearch(snippet)
})

// when user picks or clears selection
watch(selected, suggestion => {
  const inputEl = document.getElementById(props.id)
  if (inputEl) inputEl.setAttribute('aria-expanded', 'false')
  if (!suggestion) {
    search.value = null
  }
  props.onSelectResult(suggestion)
})

// manage aria-expanded & aria-controls when suggestions appear/disappear
watch(suggestions, (newVal, oldVal) => {
  const combo = autocomplete.value?.$el.querySelector('[role="combobox"]')
  const inputEl = document.getElementById(props.id)
  if (inputEl && newVal.length && !oldVal.length) {
    nextTick(() => {
      const listboxId = combo?.getAttribute('aria-owns')
      const listbox   = listboxId && document.getElementById(listboxId)
      inputEl.setAttribute('aria-expanded', 'true')
      listboxId && inputEl.setAttribute('aria-controls', listboxId)
      listbox && listbox.setAttribute('aria-label', props.menuLabel)
    })
  } else if (inputEl && !newVal.length) {
    inputEl.setAttribute('aria-expanded', 'false')
  }
})

// blur: pick first suggestion if none chosen
function onBlur() {
  if (!isSearching.value && search.value && suggestions.value.length && !selected.value) {
    selected.value = suggestions.value[0]
    search.value = toLabel(selected.value)
  }
}

// focus: reset aria-expanded
function onFocus() {
  if (!suggestions.value.length) {
    document.getElementById(props.id)
      ?.setAttribute('aria-expanded', 'false')
  }
}

// track highlighted item
function onHighlight(index) {
  highlightedItem.value = suggestions.value[index]
}

// highlight matches in dropdown
function suggest(user) {
  return toLabel(user).replace(
    searchTokenMatcher.value,
    match => `<strong>${match}</strong>`
  )
}

// build display label
function toLabel(user) {
  if (user && typeof user === 'object') {
    let label = `${user.firstName || ''} ${user.lastName || ''}`.trim()
    if (user.email) label += ` (${user.email})`
    label += ` (${user.uid})`
    return label
  }
  return ''
}

// setup MutationObserver on mount
onMounted(() => {
  const inputEl = document.getElementById(props.id)
  if (inputEl) {
    inputEl.setAttribute('aria-autocomplete', 'list')
    menuObserver.value = new MutationObserver(mutations => {
      const m = mutations.find(x => x.attributeName === 'aria-expanded')
      const expanded = m?.target.getAttribute('aria-expanded')
      if (!suggestions.value.length && expanded === 'true') {
        inputEl.setAttribute('aria-expanded', 'false')
      }
    })
    menuObserver.value.observe(inputEl, { attributes: true })
  }
})

// clean up
onBeforeUnmount(() => {
  menuObserver.value?.disconnect()
})
</script>

<style>
.autocomplete-menu {
  z-index: 210 !important;
}
.person-lookup {
  overflow-x: clip;
}
.person-lookup .v-select__selections,
.person-lookup .v-select__selections input {
  color: rgba(0, 0, 0, 0.87) !important;
}
.person-lookup.v-input--is-focused {
  appearance: auto !important;
  caret-color: #000 !important;
  color: -webkit-focus-ring-color !important;
  outline: auto !important;
  outline-color: -webkit-focus-ring-color !important;
  outline-offset: 0px !important;
  outline-style: auto !important;
}
.person-lookup.v-input--is-focused fieldset {
  border-color: unset !important;
  border-width: 1px !important;
}
</style>
