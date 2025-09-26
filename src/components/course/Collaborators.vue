<template>
  <v-row
    align="center"
    aria-label="Collaborators"
    justify="start"
    role="region"
  >
    <v-col>
      <h3>
        Collaborators
      </h3>
      <PersonLookup
        ref="personLookup"
        class="collaborator-lookup mt-1"
        :clear-errors="() => addCollaboratorError = undefined"
        :disabled="courseStore.disableButtons"
        :error-message="addCollaboratorError"
        id-prefix="collaborator-lookup"
        label=""
        list-label="collaborators"
        :on-select-result="onSelectCollaborator"
      >
        <template #append>
          <v-btn
            id="btn-collaborator-add"
            aria-label="Add Collaborator"
            class="ml-2"
            color="primary"
            :disabled="!pendingCollaborator"
            text="Add"
            variant="flat"
            @click="addCollaborator"
          />
        </template>
      </PersonLookup>
      <div v-if="collaborators.length" class="d-flex flex-column ml-2 mt-3">
        <span class="font-weight-medium">
          The following collaborator{{ collaborators.length === 1 ? '' : 's' }} will have editing and publishing access.
        </span>
        <v-chip
          v-for="(collaborator, index) in collaborators"
          :id="`collaborator-${collaborator.uid}`"
          :key="collaborator.uid"
          class="collaborator mt-2 text-wrap"
          density="compact"
          size="large"
        >
          {{ collaborator.firstName }} {{ collaborator.lastName }}<span v-if="collaborator.email">&nbsp;({{ collaborator.email }})</span>
          <template #append>
            <v-btn
              :id="`btn-collaborator-remove-${collaborator.uid}`"
              :aria-label="`Remove ${collaborator.firstName || ''} ${collaborator.lastName || ''} as collaborator`"
              class="ml-4"
              color="warning"
              :disabled="courseStore.disableButtons"
              rounded
              size="small"
              text="Remove"
              variant="flat"
              @click="removeCollaborator(collaborator.uid, index)"
            />
          </template>
        </v-chip>
      </div>
    </v-col>
  </v-row>
</template>

<script lang="ts" setup>
import {ref} from 'vue'
import type {Collaborator} from '@/lib/types'
import {alertScreenReader, putFocusNextTick} from '@/lib/utils'
import {useCourseStore} from '@/stores/course'
import PersonLookup from '@/components/util/PersonLookup.vue'

const collaborators = defineModel({required: true, type: Array<Collaborator>})

const courseStore = useCourseStore()
const addCollaboratorError = ref<string | undefined>()
const pendingCollaborator = ref<Collaborator | undefined>()
const personLookup = ref()

const addCollaborator = () => {
  if (pendingCollaborator.value) {
    const collaborator = pendingCollaborator.value.raw
    const exists = collaborators.value.some(c => c.uid === collaborator.uid)
    if (exists) {
      addCollaboratorError.value = `${collaborator.firstName} ${collaborator.lastName} is already a collaborator.`
    } else {
      pendingCollaborator.value = undefined
      addCollaboratorError.value = undefined
      collaborators.value.push(collaborator)
      personLookup.value.selected = null
      alertScreenReader(`${collaborator.firstName} ${collaborator.lastName} added as a collaborator.`)
    }
    putFocusNextTick('collaborator-lookup-input')
  }
}

const onSelectCollaborator = collaborator => {
  pendingCollaborator.value = collaborator
  addCollaboratorError.value = undefined
}

const removeCollaborator = (uid: string, index: number) => {
  const collaborator = collaborators.value.find(c => c.uid === uid)
  if (collaborator) {
    collaborators.value = collaborators.value.filter(c => c.uid !== uid)
    alertScreenReader(`${collaborator.firstName} ${collaborator.lastName} removed.`)
    const nextId = collaborators.value[index]?.uid || null
    putFocusNextTick(nextId ? `btn-collaborator-remove-${nextId}` : 'collaborator-lookup-input')
  }
}
</script>

<style scoped>
.collaborator {
  height: fit-content !important;
  min-height: var(--v-chip-height) !important;
  width: fit-content;
}
.collaborator-lookup {
  max-width: 45rem;
}
</style>
