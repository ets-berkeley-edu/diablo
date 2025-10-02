<template>
  <v-row
    align="center"
    aria-label="Collaborators"
    role="region"
  >
    <v-col>
      <h3>
        Collaborators
      </h3>
      <v-expand-transition>
        <PersonLookup
          v-if="isEditing"
          ref="personLookup"
          class="collaborator-lookup mt-1"
          :clear-errors="() => error = undefined"
          :disabled="isSaving"
          :error-message="error"
          id-prefix="collaborator-lookup"
          label=""
          list-label="collaborators"
          :on-select-result="onSelect"
        >
          <template #append>
            <v-btn
              id="btn-collaborator-add"
              aria-label="Add Collaborator"
              class="ml-2"
              color="primary"
              :disabled="!stagedCollaborator"
              text="Add"
              variant="flat"
              @click="addCollaborator"
            />
          </template>
        </PersonLookup>
      </v-expand-transition>
      <div v-if="collaborators.length" class="d-flex flex-column ml-2 mt-3">
        <span class="font-weight-medium">
          Editing and publishing access granted to:
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
          <template v-if="course.hasOptedIn && isEditing" #append>
            <v-btn
              :id="`btn-collaborator-remove-${collaborator.uid}`"
              :aria-label="`Remove ${collaborator.firstName || ''} ${collaborator.lastName || ''} as collaborator`"
              class="ml-4"
              color="warning"
              rounded
              size="small"
              text="Remove"
              variant="flat"
              @click="removeCollaborator(collaborator.uid, index)"
            />
          </template>
        </v-chip>
      </div>
      <div class="ml-2">
        <div v-if="isEditing" class="mt-3">
          <ProgressButton
            id="btn-collaborators-save"
            :action="update"
            aria-label="Save collaborators"
            density="comfortable"
            :disabled="isSaving"
            :in-progress="isSaving"
            :text="isSaving ? 'Saving' : 'Save'"
          />
          <v-btn
            id="btn-collaborators-cancel"
            aria-label="Cancel edit"
            class="ml-2"
            density="comfortable"
            :disabled="isSaving"
            text="Cancel"
            variant="outlined"
            @click="cancel"
          />
        </div>
        <div v-if="!isEditing" class="mt-3">
          <v-btn
            id="btn-collaborators-edit"
            aria-label="Edit collaborators"
            color="primary"
            density="comfortable"
            :disabled="disableButtons || !course.hasOptedIn"
            text="Edit"
            @click="edit"
          />
        </div>
      </div>
    </v-col>
  </v-row>
</template>

<script lang="ts" setup>
import {cloneDeep, find, map} from 'lodash'
import {onMounted, ref} from 'vue'
import {storeToRefs} from 'pinia'
import type {Collaborator} from '@/lib/types'
import {alertScreenReader, putFocusNextTick} from '@/lib/utils'
import {useCourseStore} from '@/stores/course'
import PersonLookup from '@/components/util/PersonLookup.vue'
import {updateCollaborators} from '@/api/course'
import ProgressButton from '@/components/util/ProgressButton.vue'

const courseStore = useCourseStore()
const {course, disableButtons} = storeToRefs(courseStore)
const collaborators = ref<Collaborator[]>([])
const error = ref<string | undefined>()
const isEditing = ref(false)
const isSaving = ref(false)
const personLookup = ref()
const stagedCollaborator = ref<Collaborator | undefined>()

onMounted(() => {
  collaborators.value = cloneDeep(course.value.collaborators)
})

const addCollaborator = () => {
  if (stagedCollaborator.value) {
    if (collaborators.value.some(c => c.uid === stagedCollaborator.value.uid)) {
      error.value = `${stagedCollaborator.value.firstName} ${stagedCollaborator.value.lastName} is already a collaborator.`
    } else {
      collaborators.value.push(stagedCollaborator.value)
      stagedCollaborator.value = undefined
      error.value = undefined
      personLookup.value.selected = null
    }
    putFocusNextTick('collaborator-lookup-input')
  }
}

const cancel = () => {
  collaborators.value = cloneDeep(course.value.collaborators)
  isEditing.value = false
  courseStore.setDisableButtons(false)
  alertScreenReader('Update canceled')
}

const edit = () => {
  courseStore.setDisableButtons(true)
  isEditing.value = true
  alertScreenReader('Ready to edit collaborators')
}

const onSelect = (collaborator: Collaborator) => {
  stagedCollaborator.value = collaborator
  error.value = undefined
}

const removeCollaborator = (uid: string, index: number) => {
  const collaborator = find(collaborators.value, ['uid', uid])
  if (collaborator) {
    collaborators.value = collaborators.value.filter(c => c.uid !== uid)
    alertScreenReader(`${collaborator.firstName} ${collaborator.lastName} removed.`)
    const nextUID = collaborators[index]?.uid
    putFocusNextTick(nextUID ? `btn-collaborator-remove-${nextUID}` : 'collaborator-lookup-input')
  }
}

const update = () => {
  const uids = map(collaborators.value, 'uid')
  updateCollaborators(course.value.sectionId, course.value.termId, uids).then(data => {
    courseStore.setCourse(data)
    collaborators.value = cloneDeep(course.value.collaborators)
    isEditing.value = false
    courseStore.setDisableButtons(false)
    alertScreenReader('Collaborators updated.')
  })
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
