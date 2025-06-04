<template>
  <div :id="`${idPrefix}-container`" class="w-100">
    <component
      :is="isAutocomplete ? 'v-autocomplete' : 'v-combobox'"
      :id="`${idPrefix}-input`"
      ref="container"
      v-model="model"
      :aria-describedby="undefined"
      :aria-description="ariaDescription"
      :autocomplete="autocomplete"
      :base-color="color"
      bg-color="surface"
      :color="color"
      density="compact"
      :disabled="disabled"
      :error="isInvalid"
      hide-details
      hide-no-data
      :items="items"
      :list-props="{ariaLive: 'off'}"
      :loading="isBusy"
      :menu-icon="null"
      :menu-props="menuProps"
      :no-filter="isAutocomplete"
      :placeholder="placeholder || label"
      return-object
      type="text"
      variant="outlined"
      @blur.stop.prevent="onBlur"
      @keydown.enter.stop.prevent="onKeyEnter"
      @update:focused="onFocusInput"
      @update:menu="onToggleMenu"
      @update:model-value="onUpdateModel"
      @update:search="onUpdateSearch"
    >
      <template #loader="{isActive}">
        <v-progress-circular
          v-if="isActive"
          class="mr-5"
          color="primary"
          indeterminate
          size="x-small"
          width="2"
        />
      </template>
      <template #item="{index, item}">
        <v-list-item
          :id="`${idPrefix}-option-${index}`"
          :aria-selected="index === focusedListItemIndex"
          class="font-size-18"
          @click="() => onSelectItem(item)"
          @focus="e => onFocusListItem(e, index)"
        >
          <span v-html="highlightQuery(item.props.title)" />
        </v-list-item>
      </template>
      <template v-if="isAutocomplete" #selection="{item}">
        <span class="overflow-hidden text-no-wrap truncate-with-ellipsis">
          {{ item.props.title }}
        </span>
      </template>
    </component>
  </div>
</template>

<script setup>
import {filter, includes, size} from 'lodash'
import {nextTick, onMounted, onUpdated, ref} from 'vue'
import {alertScreenReader, escapeForRegExp, pluralize} from '@/lib/utils'

const props = defineProps({
  ariaDescription: {
    default: 'Expect auto-suggest.',
    required: false,
    type: String
  },
  autocomplete: {
    default: 'list',
    required: false,
    type: String
  },
  color: {
    default: 'on-surface',
    required: false,
    type: String
  },
  disabled: {
    required: false,
    type: Boolean
  },
  filterResults: {
    default: () => {},
    required: false,
    type: Function
  },
  getValue: {
    required: true,
    type: Function
  },
  idPrefix: {
    required: true,
    type: String
  },
  isAutocomplete: {
    required: false,
    type: Boolean
  },
  isBusy: {
    required: false,
    type: Boolean
  },
  isInvalid: {
    required: false,
    type: Boolean
  },
  items: {
    required: true,
    type: Array
  },
  label: {
    required: true,
    type: String
  },
  listLabel: {
    required: true,
    type: String
  },
  onClear: {
    default: () => {},
    required: false,
    type: Function
  },
  placeholder: {
    default: undefined,
    required: false,
    type: String
  },
  setValue: {
    required: true,
    type: Function
  },
  whenItemSelected: {
    default: () => {},
    required: false,
    type: Function
  }
})

const container = ref()
const focusedListItemIndex = ref()
const menuProps = ref({})
const model = defineModel({
  get() {
    return props.getValue()
  },
  set(v) {
    props.setValue(v)
  },
  type: Object
})
const query = ref('')
const resultsSummaryInterval = ref()

onMounted(() => {
  nextTick(() => {
    const combobox = getComboboxElement()
    const observer = new MutationObserver((mutations) => {
      for (const m of mutations) {
        if (includes(['aria-controls', 'aria-expanded', 'aria-haspopup'], m.attributeName)) {
          combobox.removeAttribute(m.attributeName)
        }
      }
    })
    if (combobox) {
      combobox.setAttribute('role', 'none')
      observer.observe(combobox, {attributes: true})
    }
    const input = getInputElement()
    if (input) {
      input.setAttribute('role', 'combobox')
      input.setAttribute('aria-autocomplete', 'list')
      input.setAttribute('aria-controls', `${props.idPrefix}-menu`)
      input.setAttribute('aria-expanded', false)
      input.setAttribute('aria-label', props.label)
    }
    menuProps.value = {
      id: `${props.idPrefix}-menu`,
      closeOnContentClick: true,
      eager: true
    }
  })
})

onUpdated(() => {
  const combobox = getComboboxElement()
  if (combobox) {
    combobox.removeAttribute('aria-controls')
    combobox.removeAttribute('aria-expanded')
    combobox.removeAttribute('aria-haspopup')
  }
})

const getComboboxElement = () => {
  const container = document.getElementById(`${props.idPrefix}-container`)
  return container ? container.querySelector('.v-field') : null
}

const getInputElement = () => {
  return document.getElementById(`${props.idPrefix}-input`)
}

const highlightQuery = suggestion => {
  if (suggestion) {
    const regex = new RegExp(escapeForRegExp(query.value), 'i')
    const match = suggestion.match(regex)
    if (!match) {
      return suggestion
    }
    const matchedText = suggestion.substring(match.index, match.index + match[0].toString().length)
    return suggestion.replace(regex, `<strong>${matchedText}</strong>`)
  }
}

const onBlur = () => {
  const input = getInputElement()
  input.removeAttribute('aria-activedescendant')
  focusedListItemIndex.value = null
}

const onFocusInput = isFocused => {
  if (isFocused) {
    const input = getInputElement()
    input.removeAttribute('aria-activedescendant')
    focusedListItemIndex.value = null
  }
}

const onFocusListItem = (event, index) => {
  const input = getInputElement()
  input.setAttribute('aria-activedescendant', event.target.id)
  focusedListItemIndex.value = index
}

const onKeyEnter = () => {
  clearInterval(resultsSummaryInterval.value)
}

const onSelectItem = item => {
  clearInterval(resultsSummaryInterval.value)
  model.value = item.raw
  query.value = ''
  container.value.search = ''
  nextTick(() => props.whenItemSelected(model.value))
}

const onToggleMenu = isOpen => {
  nextTick(() => {
    const input = getInputElement()
    if (isOpen) {
      const menu = document.getElementById(`${props.idPrefix}-menu`)
      const listbox = menu && menu.querySelector('[role="listbox"]')
      if (listbox) {
        listbox.setAttribute('aria-label', props.listLabel)
      }
      input.setAttribute('aria-expanded', true)
    } else {
      clearInterval(resultsSummaryInterval.value)
      input.setAttribute('aria-expanded', false)
      input.removeAttribute('aria-activedescendant')
    }
  })
}

const onUpdateModel = v => {
  if (!size(v)) {
    props.onClear()
  }
}

const onUpdateSearch = q => {
  query.value = q
  props.filterResults(q)
  clearInterval(resultsSummaryInterval.value)
  if (size(q)) {
    resultsSummaryInterval.value = setInterval(summarizeResults, 1000)
  }
}

const summarizeResults = () => {
  clearInterval(resultsSummaryInterval.value)
  if (!props.isBusy) {
    const menuOverlay = document.getElementById(`${props.idPrefix}-menu`)
    const listbox = menuOverlay && menuOverlay.querySelector('[role="listbox"]')
    if (listbox ) {
      const suggestions = filter(listbox.children, child => includes(child.classList, 'v-list-item'))
      alertScreenReader(pluralize('result', suggestions.length))
    }
  }
}
</script>

<style>
.v-autocomplete .v-field .v-field__input {
  flex-wrap: nowrap !important;
}
</style>
