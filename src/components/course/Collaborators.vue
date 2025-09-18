<template>
  <v-row
    align="center"
    aria-label="Collaborators"
    justify="start"
    role="region"
  >
    <v-col
      v-if="!isEditing"
      id="collaborators-list"
      cols="12"
    >
      <h3 id="collaborators-header">
        <span :aria-hidden="true">Collaborator(s)</span><span class="sr-only">Collaborators</span> listed will have editing and publishing access:
      </h3>
      <div class="pl-4">
        <div
          v-for="collaborator in course.collaborators"
          :id="`collaborator-${collaborator.uid}`"
          :key="`collaborator-${collaborator.uid}`"
          class="mt-2"
        >
          {{ collaboratorLabel(collaborator) }}
        </div>
        <div v-if="isEmpty(course.collaborators)" id="collaborators-none" class="mt-2 text-medium-emphasis">
          No collaborators
        </div>
        <v-btn
          id="btn-collaborators-edit"
          aria-label="Edit Collaborators"
          class="elevation-1 mt-2"
          :disabled="courseStore.disableButtons"
          text="Edit"
          variant="outlined"
          @click="toggleIsEditing"
        />
      </div>
    </v-col>
    <v-col v-if="isEditing">
      <v-card class="bg-surface-light border-sm elevation-0 w-100">
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
          <v-row>
            <v-col class="pt-0">
              <PersonLookup
                ref="personLookup"
                class="collaborator-lookup"
                :clear-errors="() => addCollaboratorError = undefined"
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
                    color="primary"
                    :disabled="!pendingCollaborator"
                    text="Add"
                    variant="flat"
                    @click="addCollaborator"
                  />
                </template>
              </PersonLookup>
            </v-col>
          </v-row>
          <v-row
            v-if="isEditing"
            align="center"
            justify="start"
            no-gutters
          >
            <v-col class="d-flex flex-column" cols="12">
              <v-chip
                v-for="(collaborator, index) in collaborators"
                :id="`collaborator-${collaborator.uid}`"
                :key="collaborator.uid"
                class="collaborator mt-4 pl-4 pr-2 text-wrap"
                size="large"
              >
                {{ collaboratorLabel(collaborator) }}
                <template #append>
                  <v-btn
                    :id="`btn-collaborator-remove-${collaborator.uid}`"
                    :aria-label="`Remove ${collaborator.firstName || ''} ${collaborator.lastName || ''} as collaborator`"
                    class="ml-4"
                    color="warning"
                    :disabled="isSaving"
                    rounded
                    size="small"
                    text="Remove"
                    variant="flat"
                    @click="removeCollaborator(collaborator.uid, index)"
                  />
                </template>
              </v-chip>
              <div class="mt-5">
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
                  class="ml-1"
                  :disabled="isSaving"
                  text="Cancel"
                  variant="text"
                  @click="cancel"
                />
              </div>
            </v-col>
          </v-row>
        </v-container>
      </v-card>
    </v-col>
  </v-row>
</template>

<script lang="ts" setup>
import {computed, ref, watch} from 'vue'
import {differenceBy, isEmpty, size} from 'lodash'
import {storeToRefs} from 'pinia'
import type {Collaborator} from '@/lib/types'
import {alertScreenReader, putFocusNextTick} from '@/lib/utils'
import {updateCollaborators} from '@/api/course'
import {useCourseStore} from '@/stores/course'
import PersonLookup from '@/components/util/PersonLookup.vue'
import ProgressButton from '@/components/util/ProgressButton.vue'

const props = defineProps({
  setModel: {
    required: true,
    type: Function
  }
})

const courseStore = useCourseStore()
const {course} = storeToRefs(courseStore)
const addCollaboratorError = ref<string | undefined>()
const collaborators = ref<Collaborator[]>([])
const hasChanges = computed(() => {
  return size(collaborators.value) !== size(course.value.collaborators) || !!size(differenceBy(collaborators.value, course.value.collaborators, 'uid'))
})
const isEditing = ref(false)
const isSaving = ref(false)
const pendingCollaborator = ref<Collaborator | undefined>()
const personLookup = ref()

watch(isEditing, courseStore.setDisableButtons)
watch(isSaving, courseStore.setDisableButtons)

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

const cancel = () => {
  alertScreenReader('Collaborator edit cancelled.')
  putFocusNextTick('btn-collaborators-edit')
  isEditing.value = false
  isSaving.value = false
  pendingCollaborator.value = undefined
  addCollaboratorError.value = undefined
}

const collaboratorLabel = (collaborator) => {
  let label = `${collaborator.firstName} ${collaborator.lastName}`
  if (collaborator.email) label += ` (${collaborator.email})`
  return `${label} (${collaborator.uid})`
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

const save = () => {
  isSaving.value = true
  updateCollaborators(
    collaborators.value.map(c => c.uid),
    course.value.sectionId,
    course.value.termId
  ).then(data => {
    alertScreenReader('Collaborators updated.')
    putFocusNextTick('btn-collaborators-edit')
    props.setModel(data.collaborators)
    isEditing.value = false
    isSaving.value = false
    addCollaboratorError.value = undefined
  })
}

const toggleIsEditing = () => {
  collaborators.value = [...course.value.collaborators]
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
