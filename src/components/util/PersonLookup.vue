<template>
  <div :class="containerClass">
    <div :class="{'col col-4': inline}">
      <label
        :id="`${id}-label`"
        :for="id"
        :class="labelClass"
      >
        <span v-if="label">{{ label }}</span>
        <span v-if="placeholder" class="sr-only">{{ placeholder }}</span>
      </label>
    </div>
    <div :class="{'col col-6': inline, 'pt-1': !inline}">
      <v-autocomplete
        :id="id"
        ref="autocomplete"
        v-model="selected"
        :allow-overflow="false"
        :append-icon="null"
        :aria-disabled="disabled"
        :aria-label="toLabel(selected)"
        auto-select-first
        background-color="white"
        class="person-lookup"
        :class="inputClass"
        dense
        :disabled="disabled"
        :error="!!errorMessage"
        :error-messages="errorMessage && [errorMessage]"
        hide-details
        :hide-no-data="isSearching || !search"
        :items="suggestions"
        light
        :loading="isSearching ? 'tertiary' : false"
        :menu-props="menuProps"
        no-data-text="No results found."
        no-filter
        outlined
        :placeholder="placeholder"
        return-object
        :search-input.sync="search"
        single-line
        @blur="onBlur"
        @focus="onFocus"
        @update:list-index="onHighlight"
      >
        <template #selection="data">
          <span class="text-nowrap">{{ toLabel(data.item) }}</span>
        </template>
        <template #item="data">
          <v-list-item
            v-bind="data.attrs"
            :aria-selected="data.item === highlightedItem"
            class="tertiary--text"
            v-on="data.on"
          >
            <v-list-item-content>
              <span v-html="suggest(data.item)" />
            </v-list-item-content>
          </v-list-item>
        </template>
      </v-autocomplete>
    </div>
    <div :class="{'col col-2 pl-0': inline}">
      <div
        v-if="errorMessage"
        :id="`${id}-error`"
        class="v-messages error--text px-3 mt-1"
        :class="$vuetify.theme.dark ? 'text--lighten-2' : ''"
        role="alert"
      >
        {{ errorMessage }}
      </div>
    </div>
  </div>
</template>

<script>
import {searchUsers} from '@/api/user'

export default {
  name: 'PersonLookup',
  props: {
    disabled: {
      required: false,
      type: Boolean
    },
    errorMessage: {
      default: undefined,
      required: false,
      type: String
    },
    id: {
      default: 'input-person-lookup-autocomplete',
      required: false,
      type: String
    },
    inline: {
      required: false,
      type: Boolean
    },
    inputClass: {
      default: undefined,
      required: false,
      type: String
    },
    label: {
      default: null,
      required: false,
      type: String
    },
    labelClass: {
      default: null,
      required: false,
      type: String
    },
    menuLabel: {
      required: true,
      type: String
    },
    onSelectResult: {
      default: () => {},
      required: false,
      type: Function
    },
    placeholder: {
      default: 'Name or UID',
      required: false,
      type: String
    }
  },
  data: () => ({
    highlightedItem: undefined,
    isSearching: false,
    menuObserver: undefined,
    menuProps: {
      contentClass: 'v-sheet--outlined autocomplete-menu'
    },
    search: undefined,
    searchTokenMatcher: undefined,
    selected: undefined,
    suggestions: [],
  }),
  computed: {
    containerClass() {
      return this.inline ? 'row d-flex align-center row--dense' : 'd-flex flex-column flex-grow-1'
    }
  },
  watch: {
    search(snippet) {
      this.isSearching = true
      this.debouncedSearch(snippet)
    },
    selected(suggestion) {
      const inputEl = document.getElementById(this.id)
      inputEl.setAttribute('aria-expanded', 'false')
      if (!suggestion) {
        this.search = null
      }
      this.onSelectResult(suggestion)
    },
    suggestions(newValue, oldValue) {
      // When the popup listbox of suggestions appears, correct faulty attributes according to
      // https://www.w3.org/WAI/ARIA/apg/patterns/combobox/examples/combobox-autocomplete-list/
      const combobox = this.$refs.autocomplete.$el ? this.$refs.autocomplete.$el.querySelector('[role="combobox"]') : null
      const inputEl = document.getElementById(this.id)
      if (inputEl && newValue.length && !oldValue.length) {
        this.$nextTick(() => {
          const listboxId = combobox.getAttribute('aria-owns')
          const listbox = document.getElementById(listboxId)
          inputEl.setAttribute('aria-expanded', 'true')
          if (listboxId) {
            inputEl.setAttribute('aria-controls', listboxId)
          }
          if (listbox) {
            listbox.setAttribute('aria-label', this.menuLabel)
          }
        })
      } else if (inputEl && !newValue.length) {
        inputEl.setAttribute('aria-expanded', 'false')
      }
    }
  },
  methods: {
    clear() {
      this.selected = null
    },
    executeSearch(snippet) {
      if (snippet) {
        searchUsers(snippet).then(results => {
          const searchTokens = this.$_.split(this.$_.trim(snippet), /\W/g)
          this.searchTokenMatcher = RegExp(this.$_.join(searchTokens, '|'), 'gi')
          this.suggestions = results
          this.isSearching = false
        })
      } else {
        this.isSearching = false
        this.searchTokenMatcher = null
        this.selected = null
        this.suggestions = []
      }
    },
    onBlur() {
      if (!this.isSearching && !!this.search && this.suggestions.length && !this.selected) {
        this.selected = this.suggestions[0]
        this.search = this.toLabel(this.selected)
      }
    },
    onFocus() {
      if (!this.suggestions.length) {
        const inputEl = document.getElementById(this.id)
        inputEl.setAttribute('aria-expanded', 'false')
      }
    },
    onHighlight(index) {
      this.highlightedItem = this.suggestions[index]
    },
    suggest(user) {
      return this.toLabel(user).replace(this.searchTokenMatcher, match => `<strong>${match}</strong>`)
    },
    toLabel(user) {
      if (user && user instanceof Object) {
        let label = `${user.firstName || ''} ${user.lastName || ''}`
        if (user.email) {
          label += ` (${user.email})`
        }
        label += ` (${user.uid})`
        return label
      } else {
        return
      }
    }
  },
  created() {
    this.debouncedSearch = this.$_.debounce(this.executeSearch, 300)
  },
  mounted() {
    // Vuetify sets aria-expanded="true" on the element prematurely, before the user enters any text.
    // It should be set when the popup listbox containing suggestions appears. This workaround listens
    // for the value of aria-expanded to change and corrects it if necessary.
    const inputEl = document.getElementById(this.id)
    if (inputEl) {
      inputEl.setAttribute('aria-autocomplete', 'list')
      this.menuObserver = new MutationObserver((mutations) => {
        const ariaExpandedMutation = this.$_.find(mutations, {attributeName: 'aria-expanded'})
        const ariaExpanded = ariaExpandedMutation ? ariaExpandedMutation.target.getAttribute('aria-expanded') : null
        if (!this.suggestions.length && ariaExpanded === 'true') {
          inputEl.setAttribute('aria-expanded', 'false')
        }
      })
      this.menuObserver.observe(inputEl, {attributes: true})
    }
  },
  beforeUnmount() {
    if (this.menuObserver) {
      this.menuObserver.disconnect()
    }
  }
}
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
