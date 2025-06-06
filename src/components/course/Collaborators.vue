<template>
  <v-row
    align="center"
    aria-labelledby="collaborators-header"
    justify="start"
    role="region"
  >
    <v-col
      v-if="!isEditing"
      id="collaborators-list"
      class="px-4 my-2"
      cols="12"
    >
      <h3 id="collaborators-header">
        Collaborator(s) listed will have editing and publishing access:
      </h3>
      <div
        v-for="collaborator in course.collaborators"
        :id="`collaborator-${collaborator.uid}`"
        :key="`collaborator-${collaborator.uid}`"
        class="pl-4 pt-2"
      >
        {{ collaboratorLabel(collaborator) }}
      </div>
      <div v-if="isEmpty(course.collaborators)" id="collaborators-none" class="pl-4 pt-2 text-medium-emphasis">
        No collaborators
      </div>
      <v-btn
        id="btn-collaborators-edit"
        aria-label="Edit Collaborators"
        class="mt-3"
        @click="toggleIsEditing"
      >
        Edit
      </v-btn>
    </v-col>
    <v-card v-if="isEditing" class="bg-surface-light my-2 w-100">
      <v-container>
        <v-row
          align="center"
          aria-live="polite"
          justify="start"
        >
          <v-col class="px-3" cols="12">
            <h3>
              Update collaborators
            </h3>
          </v-col>
        </v-row>
        <v-row align="end" justify="start">
          <v-col>
            <PersonLookup
              ref="personLookup"
              class="collaborator-lookup"
              :clear-errors="() => addCollaboratorError = null"
              :disabled="isSaving"
              :error-message="addCollaboratorError"
              id-prefix="collaborator-lookup"
              label="Find collaborator"
              list-label="collaborators"
              :on-select-result="onSelectCollaborator"
            >
              <template #append>
                <v-btn
                  id="btn-collaborator-add"
                  aria-label="Add Collaborator"
                  class="ml-2"
                  color="success"
                  :disabled="!pendingCollaborator"
                  variant="flat"
                  @click="addCollaborator"
                >
                  Add
                </v-btn>
              </template>
            </PersonLookup>
          </v-col>
        </v-row>
        <v-row
          v-if="isEditing"
          align="center"
          justify="start"
        >
          <v-col class="d-flex flex-column" cols="12">
            <v-chip
              v-for="(collaborator, index) in collaborators"
              :id="`collaborator-${collaborator.uid}`"
              :key="collaborator.uid"
              class="collaborator my-2 pl-4 pr-2 py-2 text-wrap"
              size="large"
            >
              {{ collaboratorLabel(collaborator) }}
              <template #append>
                <v-btn
                  :id="`btn-collaborator-remove-${collaborator.uid}`"
                  :aria-label="`Remove ${collaborator.firstName || ''} ${collaborator.lastName || ''} as collaborator`"
                  class="ml-4"
                  :disabled="isSaving"
                  rounded
                  size="small"
                  variant="flat"
                  @click="removeCollaborator(collaborator.uid, index)"
                >
                  Remove
                </v-btn>
              </template>
            </v-chip>
            <div class="mt-4">
              <ProgressButton
                id="btn-collaborators-save"
                :action="save"
                aria-label="Save Collaborators"
                :disabled="!hasChanges || isSaving"
                :in-progress="isSaving"
                :text="isSaving ? 'Saving' : 'Save'"
              />
              <v-btn
                id="btn-collaborators-cancel"
                aria-label="Cancel Collaborator Edit"
                class="ml-2"
                :disabled="isSaving"
                variant="text"
                @click="cancel"
              >
                Cancel
              </v-btn>
            </div>
          </v-col>
        </v-row>
      </v-container>
    </v-card>
  </v-row>
</template>

<script setup>
import {computed, ref} from 'vue'
import {differenceBy, isEmpty, size} from 'lodash'
import {alertScreenReader, putFocusNextTick} from '@/lib/utils'
import PersonLookup from '@/components/util/PersonLookup'
import ProgressButton from '@/components/util/ProgressButton'
import {updateCollaborators} from '@/api/course'

const props = defineProps({
  course: {
    required: true,
    type: Object
  },
  setModel: {
    required: true,
    type: Function
  }
})

const addCollaboratorError = ref()
const collaborators = ref([])
const isEditing = ref(false)
const isSaving = ref(false)
const pendingCollaborator = ref()
const personLookup = ref()

const hasChanges = computed(() => {
  return size(collaborators.value) !== size(props.course.collaborators) || !!size(differenceBy(collaborators.value, props.course.collaborators, 'uid'))
})
const addCollaborator = () => {
  if (pendingCollaborator.value) {
    const collaborator = pendingCollaborator.value.raw
    const exists = collaborators.value.some(c => c.uid === collaborator.uid)
    if (exists) {
      addCollaboratorError.value = `${collaborator.firstName} ${collaborator.lastName} is already a collaborator.`
    } else {
      pendingCollaborator.value = null
      addCollaboratorError.value = null
      collaborators.value.push(collaborator)
      personLookup.value.selected = null
      alertScreenReader(`${collaborator.firstName} ${collaborator.lastName} added as a collaborator.`)
    }
    putFocusNextTick('collaborator-lookup-input')
  }
}

const cancel = () => {
  alertScreenReader('Collaborator edit cancelled.')
  putFocusNextTick('btn-collaborators-edit')
  isEditing.value = false
  isSaving.value = false
  pendingCollaborator.value = null
  addCollaboratorError.value = null
}

const collaboratorLabel = (collaborator) => {
  let label = `${collaborator.firstName} ${collaborator.lastName}`
  if (collaborator.email) label += ` (${collaborator.email})`
  return `${label} (${collaborator.uid})`
}

const onSelectCollaborator = collaborator => {
  pendingCollaborator.value = collaborator
  addCollaboratorError.value = null
}

const removeCollaborator = (uid, index) => {
  const collaborator = collaborators.value.find(c => c.uid === uid)
  collaborators.value = collaborators.value.filter(c => c.uid !== uid)
  alertScreenReader(`${collaborator.firstName} ${collaborator.lastName} removed.`)
  const nextId = collaborators.value[index]?.uid || null
  putFocusNextTick(nextId ? `btn-collaborator-remove-${nextId}` : 'collaborator-lookup-input')
}

const save = () => {
  isSaving.value = true
  updateCollaborators(
    collaborators.value.map(c => c.uid),
    props.course.sectionId,
    props.course.termId
  ).then(course => {
    alertScreenReader('Collaborators updated.')
    putFocusNextTick('btn-collaborators-edit')
    props.setModel(course.collaborators)
    isEditing.value = false
    isSaving.value = false
    addCollaboratorError.value = null
  })
}

const toggleIsEditing = () => {
  collaborators.value = [...props.course.collaborators]
  isEditing.value = true
  putFocusNextTick('collaborator-lookup-input')
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
