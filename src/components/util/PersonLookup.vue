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
      <AccessibleCombobox
        id-prefix="search-options-find-instructor"
        aria-description="Instructor name or S I D or email lookup. Expect auto suggest."
        autocomplete="off"
        :clazz="{'mt-1 text-black': true}"
        :clearable="!isSearching"
        color="primary"
        density="compact"
        :filter-results="executeSearch"
        :get-value="() => get(selected, 'label')"
        :set-value="s => selected = s.raw"
        is-autocomplete
        :is-busy="isSearching"
        :items="formattedItems"
        item-title="title"
        label="Find Instructor by:"
        list-label="Instructor List"
        :maxlength="56"
        min-width="12rem"
        :on-clear="onClearSearch"
        placeholder="Enter name, email, or SID ..."
      />
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
import AccessibleCombobox from '@/components/util/AccessibleCombobox'
import {get} from 'lodash'

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
  const inputEl = document.getElementById(props.id)
  if (inputEl) inputEl.setAttribute('aria-expanded', 'false')
  if (!suggestion) {
    search.value = null
  }
  props.onSelectResult(suggestion)
})

watch(suggestions, (newVal, oldVal) => {
  const combo = autocomplete.value?.$el.querySelector('[role="combobox"]')
  const inputEl = document.getElementById(props.id)
  if (inputEl && newVal.length && !oldVal.length) {
    nextTick(() => {
      const listboxId = combo?.getAttribute('aria-owns')
      const listbox = listboxId && document.getElementById(listboxId)
      inputEl.setAttribute('aria-expanded', 'true')
      listboxId && inputEl.setAttribute('aria-controls', listboxId)
      listbox && listbox.setAttribute('aria-label', props.menuLabel)
    })
  } else if (inputEl && !newVal.length) {
    inputEl.setAttribute('aria-expanded', 'false')
  }
})

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
