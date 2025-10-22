<template>
  <v-row
    align="center"
    aria-labelledby="publish-type-header"
    justify="start"
    role="region"
  >
    <v-col cols="12">
      <div class="w-100">
        <h3 id="publish-type-header">
          <label for="select-publish-type">Recording Placement</label>
        </h3>
        <div v-if="!isEditing" class="ml-2 py-2">
          {{ publishType ? displayLabels[publishType] : 'None' }}
          <div v-if="course.canvasSites.length" class="border-sm mt-2 pa-4 pl-6">
            Linked bCourses site{{ course.canvasSites.length === 1 ? '' : 's' }}:
            <ul>
              <li v-for="canvasSite in course.canvasSites" :key="canvasSite.canvasSiteId">
                <CanvasCourseSite :course-site="canvasSite" :site-id="canvasSite.canvasSiteId" />
              </li>
            </ul>
          </div>
        </div>
        <div v-if="isEditing">
          <v-radio-group
            id="select-publish-type"
            v-model="publishType"
            :aria-activedescendant="`radio-publish-type-${publishType.replaceAll('_', '-')}`"
            color="primary"
            density="comfortable"
            hide-details
          >
            <v-radio
              v-for="publishTypeOption in publishTypeOptions"
              :id="`radio-publish-type-${publishTypeOption.replaceAll('_', '-')}`"
              :key="publishTypeOption"
              :label="displayLabels[publishTypeOption]"
              :value="publishTypeOption"
            />
          </v-radio-group>
          <v-expand-transition>
            <div
              v-if="publishType && publishType.startsWith('kaltura_media_gallery') && (currentUser.isAdmin || course.canvasSiteIds)"
              id="publish-linked-canvas-site"
              class="ml-8"
            >
              <div>
                <div v-if="!currentUser.isAdmin" class="mr-3 my-3">
                  <v-select
                    id="select-canvas-site"
                    v-model="pendingCanvasSite"
                    aria-label="Select course site"
                    autocomplete="off"
                    density="compact"
                    hide-details
                    :items="canvasSiteOptions"
                    label="Select course site"
                    :list-props="{ariaLabel: 'My bCourses sites', ariaLive: 'off', id: 'canvas-site-list'}"
                    :menu-props="{attach: menuContainer, eager: true, id: 'canvas-site-menu'}"
                    :title="undefined"
                    :value="get(pendingCanvasSite, 'title')"
                    variant="outlined"
                    @update:menu="onToggleCanvasSitesMenu"
                  >
                    <template #item="{props: itemProps, item}">
                      <v-list-item
                        :id="`menu-option-canvas-site-${item.raw.value.canvasSiteId}`"
                        :disabled="isCanvasSiteIdStaged(item.raw.value.canvasSiteId)"
                        v-bind="itemProps"
                      />
                    </template>
                    <template #append>
                      <v-btn
                        id="btn-canvas-site-add"
                        aria-label="Add bCourses Site"
                        color="primary"
                        :disabled="!pendingCanvasSite"
                        text="Add"
                        @click.stop="addCanvasSiteConfirm"
                        @keydown.enter.prevent.stop="addCanvasSiteConfirm"
                      />
                    </template>
                  </v-select>
                  <div id="canvas-site-menu-container" ref="menuContainer" />
                </div>
                <div v-if="currentUser.isAdmin" class="mt-3">
                  <v-text-field
                    id="input-canvas-site-id"
                    v-model="pendingCanvasSiteId"
                    :aria-describedby="undefined"
                    class="mt-2"
                    density="compact"
                    hide-details
                    label="Enter Canvas site ID"
                    variant="outlined"
                  >
                    <template #append>
                      <ProgressButton
                        id="btn-canvas-site-add"
                        :action="addCanvasSiteById"
                        aria-label="Add Canvas Site"
                        color="success"
                        :disabled="isFindingCanvasSite || !pendingCanvasSiteId || !/^\d+$/.test(pendingCanvasSiteId) || isCanvasSiteIdStaged(pendingCanvasSiteId)"
                        :in-progress="isFindingCanvasSite"
                        :text="isFindingCanvasSite ? 'Adding' : 'Add'"
                      />
                    </template>
                  </v-text-field>
                </div>
                <div class="d-flex flex-column pb-2">
                  <v-chip
                    v-for="(site, index) in publishCanvasSites"
                    :id="`canvas-site-${site.canvasSiteId}`"
                    :key="site.canvasSiteId"
                    class="canvas-site mt-2 pl-4 pr-2 text-wrap"
                  >
                    {{ site.name }}<span v-if="site.name !== site.courseCode">&nbsp;({{ site.courseCode }})</span>
                    <template #append>
                      <v-btn
                        :id="`btn-canvas-site-remove-${site.canvasSiteId}`"
                        :aria-label="`Remove ${site.name} (${site.courseCode})`"
                        class="ml-6"
                        color="warning"
                        rounded
                        size="small"
                        text="Remove"
                        variant="flat"
                        @click="() => removeCanvasSite(site.canvasSiteId, index)"
                      />
                    </template>
                  </v-chip>
                </div>
                <div v-if="!currentUser.isAdmin" class="font-italic mt-2 py-2 text-body-2">
                  <span class="font-weight-bold">Note:</span> To link a bCourses site from a past term,
                  please <a :href="`mailto:${config.emailCourseCaptureSupport}`" target="_blank">contact Course Capture support.</a>
                </div>
              </div>
            </div>
          </v-expand-transition>
        </div>
        <div class="ml-2">
          <div v-if="isEditing" class="mt-3">
            <ProgressButton
              id="btn-publish-type-save"
              :action="update"
              aria-label="Save Note"
              density="comfortable"
              :disabled="isSaving || publishCanvasSites.length === 0"
              :in-progress="isSaving"
              :text="isSaving ? 'Saving' : 'Save'"
            />
            <v-btn
              id="btn-publish-type-cancel"
              aria-label="Cancel Note Edit"
              class="ml-2"
              density="comfortable"
              :disabled="isSaving"
              text="Cancel"
              variant="outlined"
              @click="cancel"
            />
          </div>
          <v-expand-transition v-if="!isEditing">
            <v-btn
              v-if="canUserEdit"
              id="btn-publish-type-edit"
              aria-label="Edit collaborators"
              class="mt-2"
              color="primary"
              density="comfortable"
              :disabled="disableButtons"
              text="Edit"
              @click="edit"
            />
          </v-expand-transition>
        </div>
      </div>
    </v-col>
  </v-row>
</template>

<script lang="ts" setup>
import {each, filter, find, get, isEmpty, map, size} from 'lodash'
import {computed, onMounted, ref} from 'vue'
import {storeToRefs} from 'pinia'
import type {CanvasSite, Course} from '@/lib/types'
import {alertScreenReader, putFocusNextTick} from '@/lib/utils'
import {getCanvasSitesTeaching} from '@/api/user'
import {getCourseSite, updatePublishType} from '@/api/course'
import {useContextStore} from '@/stores/context'
import {useCourseStore} from '@/stores/course'
import CanvasCourseSite from '@/components/course/CanvasCourseSite.vue'
import ProgressButton from '@/components/util/ProgressButton.vue'

type CanvasSiteOption = {
  id: string,
  disabled: boolean,
  role: string,
  title: string,
  value: CanvasSite
}

const courseStore = useCourseStore()
const {config, currentUser} = useContextStore()
const {course, disableButtons} = storeToRefs(courseStore)
const canUserEdit = computed(() => {
  const instructor = find(course.value.instructors, ['uid', currentUser.uid])
  return (currentUser.isAdmin && !course.value.deletedAt) || get(instructor, 'hasOptedIn', false)
})
const canvasSiteOptions = ref<CanvasSiteOption[]>([])
const displayLabels = {
  kaltura_media_gallery: 'Publish to the Media Gallery (all members of the bCourses site will have access)',
  kaltura_my_media: `Place in My Media (${currentUser.isAdmin ? 'instructor' : 'I'} will decide if and how ${currentUser.isAdmin ? 'they' : 'I'} want to share)`
}
const isEditing = ref(false)
const isFindingCanvasSite = ref(false)
const isSaving = ref(false)
const menuContainer = ref()
const pendingCanvasSite = ref()
const pendingCanvasSiteId = ref<number | undefined>()
const publishCanvasSites = ref<CanvasSite[]>(course.value.canvasSites)
const publishType = ref<string>()
const publishTypeOptions = Object.keys(config.publishTypeOptions).sort().reverse()

onMounted(() => {
  publishType.value = course.value.publishType
  if (!currentUser.isAdmin && currentUser.uid) {
    getCanvasSitesTeaching(currentUser.uid).then(data => {
      each(data, canvasSite => {
        const courseCode = canvasSite.courseCode
        const name = canvasSite.name
        canvasSiteOptions.value.push({
          id: `canvas-site-option-${canvasSite.canvasSiteId}`,
          disabled: false,
          role: 'option',
          title: name === courseCode ? name : `${name} (${courseCode})`,
          value: canvasSite
        })
      })
    })
  }
})

const addCanvasSiteById = () => {
  courseStore.setDisableButtons(true)
  isFindingCanvasSite.value = true
  if (pendingCanvasSiteId.value && !isCanvasSiteIdStaged(pendingCanvasSiteId.value)) {
    getCourseSite(pendingCanvasSiteId.value).then(data => {
      if (data) {
        publishCanvasSites.value.push(data)
        isFindingCanvasSite.value = false
        pendingCanvasSiteId.value = undefined
        courseStore.setDisableButtons(false)
        alertScreenReader(`${data.name} added.`)
        putFocusNextTick('input-canvas-site-id')
      }
    })
  }
}

const addCanvasSiteConfirm = () => {
  const canvasSiteId = pendingCanvasSite.value.canvasSiteId
  if (pendingCanvasSite.value && !isCanvasSiteIdStaged(canvasSiteId)) {
    publishCanvasSites.value.push(pendingCanvasSite.value)
    alertScreenReader(`Added course site ${pendingCanvasSite.value.name}.`)
  }
  putFocusNextTick('select-canvas-site')
  pendingCanvasSite.value = null
}

const cancel = () => {
  publishType.value = course.value.publishType
  isEditing.value = false
  courseStore.setDisableButtons(false)
  alertScreenReader('Update canceled')
}

const edit = () => {
  courseStore.setDisableButtons(true)
  isEditing.value = true
  alertScreenReader('Ready to edit recording placement')
}

const isCanvasSiteIdStaged = (canvasSiteId: string) => {
  return !!find(publishCanvasSites.value, {'canvasSiteId': parseInt(canvasSiteId, 10)})
}

const onToggleCanvasSitesMenu = isOpen => {
  if (isOpen) {
    putFocusNextTick(get(canvasSiteOptions.value, '0.id', 'canvas-site-list'))
  }
}

const removeCanvasSite = (canvasSiteId: number, index: number) => {
  const nextFocusIndex = (index + 1 === size(publishCanvasSites.value)) ? index - 1 : index + 1
  const nextFocusSiteId = get(publishCanvasSites.value, `${nextFocusIndex}.canvasSiteId`)
  const canvasSite = find(publishCanvasSites.value, c => c.canvasSiteId === canvasSiteId)
  const canvasSiteName = get(canvasSite, 'name', '')
  let nextFocusId = `btn-canvas-site-remove-${nextFocusSiteId}`
  publishCanvasSites.value = filter(publishCanvasSites.value, c => c.canvasSiteId !== canvasSiteId)
  alertScreenReader(`Removed course site ${canvasSiteName}.`)
  if (isEmpty(publishCanvasSites.value) || !nextFocusSiteId) {
    nextFocusId = currentUser.isAdmin ? 'input-canvas-site-id' : 'select-canvas-site'
  }
  putFocusNextTick(nextFocusId)
}

const update = () => {
  if (publishType.value) {
    isSaving.value = true
    let canvasSiteIds: string[] = []
    if (publishType.value === 'kaltura_media_gallery') {
      canvasSiteIds = map(publishCanvasSites.value, 'canvasSiteId')
    } else {
      publishCanvasSites.value = []
    }
    updatePublishType(canvasSiteIds, publishType.value, course.value.sectionId, course.value.termId).then((data: Course) => {
      courseStore.setCourse(data)
      publishType.value = course.value.publishType
      isEditing.value = false
      isSaving.value = false
      courseStore.setDisableButtons(false)
      alertScreenReader(`Publish type is now set to ${publishType.value}`)
    })
  }
}
</script>

<style scoped>
.canvas-site {
  font-size: 16px;
  height: fit-content !important;
  min-height: var(--v-chip-height) !important;
  width: fit-content;
}
</style>
