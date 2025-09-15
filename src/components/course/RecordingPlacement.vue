<template>
  <v-row
    align="center"
    aria-labelledby="publish-type-header"
    justify="start"
    role="region"
  >
    <v-col cols="12" class="pa-4 my-2" :class="{'bg-surface-light rounded': isEditing}">
      <h3 id="publish-type-header">
        <label v-if="isEditing" for="select-publish-type">Recording Placement</label>
        <span v-if="!isEditing">Recording Placement</span>
      </h3>
      <div v-if="!isEditing" id="publish-type-name" class="pl-4 pt-2">
        {{ labels[course.publishType] }}
      </div>
      <div
        v-if="isEditing"
        id="select-publish-type"
        :aria-activedescendant="`radio-publish-type-${publishType}`"
        class="py-4"
        role="radiogroup"
        tabindex="0"
      >
        <div
          v-for="(publishTypeOption, index) in publishTypeOptions"
          :key="publishTypeOption"
          class="d-flex flex-nowrap py-1"
        >
          <input
            :id="`radio-publish-type-${publishTypeOption}`"
            :checked="publishTypeOption === publishType ? 'checked' : false"
            class="ml-1 mr-3"
            :disabled="isSaving"
            type="radio"
            :value="publishTypeOption"
            @change="() => onPublishTypeChange(publishTypeOption, index)"
          >
          <label class="font-size-16 text-medium-emphasis" :for="`radio-publish-type-${publishTypeOption}`">{{ labels[publishTypeOption] }}</label>
        </div>
      </div>
      <div
        v-if="publishType && publishType.startsWith('kaltura_media_gallery') && (course.canvasSiteIds || isEditing)"
        id="publish-linked-canvas-site"
        class="pt-4"
      >
        <h5 id="linked-course-sites-header" class="mb-2 ml-4">
          Linked bCourses <span :aria-hidden="true">site(s):</span><span class="sr-only">sites</span>
        </h5>
        <div v-if="!isEditing">
          <div v-for="site in course.canvasSites" :key="site.canvasSiteId" class="mb-2 pl-4">
            <CanvasCourseSite :site-id="site.canvasSiteId" :course-site="site" />
          </div>
        </div>
        <div v-if="isEditing">
          <div v-if="!currentUser.isAdmin" class="pa-2">
            <v-select
              id="select-canvas-site"
              v-model="pendingCanvasSite"
              aria-describedby="linked-course-sites-header"
              aria-label="Select course site"
              autocomplete="off"
              density="compact"
              :disabled="isSaving"
              hide-details
              item-props
              :items="publishCanvasSiteOptions"
              label="Select course site"
              :list-props="{ariaLabel: 'My bCourses sites', ariaLive: 'off', id: 'canvas-site-list'}"
              :menu-props="{attach: menuContainer, eager: true, id: 'canvas-site-menu'}"
              :title="undefined"
              :value="get(pendingCanvasSite, 'title')"
              variant="solo"
              @update:menu="onToggleCanvasSitesMenu"
            >
              <template #item="{props: itemProps, item}">
                <v-list-item
                  :id="`menu-option-canvas-site-${item.raw.canvasSiteId}`"
                  :disabled="isCanvasSiteIdStaged(item.raw.canvasSiteId)"
                  v-bind="itemProps"
                />
              </template>
              <template #append>
                <v-btn
                  id="btn-canvas-site-add"
                  aria-label="Add bCourses Site"
                  color="success"
                  :disabled="!pendingCanvasSite"
                  @click.stop="addCanvasSiteConfirm"
                  @keydown.enter.prevent.stop="addCanvasSiteConfirm"
                >
                  Add
                </v-btn>
              </template>
            </v-select>
            <div id="canvas-site-menu-container" ref="menuContainer" />
          </div>
          <div v-if="currentUser.isAdmin" class="pa-2">
            <v-text-field
              id="input-canvas-site-id"
              v-model="pendingCanvasSiteId"
              :aria-describedby="undefined"
              class="mt-2"
              density="compact"
              :disabled="isSaving"
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
          <div class="d-flex flex-column pa-2">
            <v-chip
              v-for="(site, index) in publishCanvasSites"
              :id="`canvas-site-${site.canvasSiteId}`"
              :key="site.canvasSiteId"
              class="canvas-site my-2 pl-4 pr-2 py-2 text-wrap"
            >
              {{ site.name }} ({{ site.courseCode }})
              <template #append>
                <v-btn
                  :id="`btn-canvas-site-remove-${site.canvasSiteId}`"
                  :aria-label="`Remove ${site.name} (${site.courseCode})`"
                  class="ml-2"
                  :disabled="isSaving"
                  rounded
                  size="small"
                  variant="flat"
                  @click="() => removeCanvasSite(site.canvasSiteId, index)"
                >
                  Remove
                </v-btn>
              </template>
            </v-chip>
          </div>
          <div v-if="!currentUser.isAdmin" class="py-2 text-body-2">
            To link a bCourses site from a past term, please <a :href="`mailto:${config.emailCourseCaptureSupport}`" target="_blank">contact Course Capture support.</a>
          </div>
        </div>
      </div>
      <v-btn
        v-if="!isEditing"
        id="btn-publish-type-edit"
        aria-label="Edit Recording Placement"
        class="mt-3"
        @click="toggleIsEditing"
      >
        Edit
      </v-btn>
      <div v-if="isEditing" class="pt-4">
        <ProgressButton
          id="btn-publish-type-save"
          :action="updatePublishTypeClicked"
          aria-label="Save Recording Placement"
          :disabled="isSaving || (publishType && publishType.startsWith('kaltura_media_gallery') && !publishCanvasSites.length)"
          :in-progress="isSaving"
          :text="isSaving ? 'Saving' : 'Save'"
        />
        <v-btn
          id="btn-publish-type-cancel"
          aria-label="Cancel Recording Placement Edit"
          class="ml-2"
          :disabled="isSaving"
          variant="text"
          @click="updatePublishTypeCancel"
        >
          Cancel
        </v-btn>
      </div>
    </v-col>
  </v-row>
</template>

<script lang="ts" setup>
import type {PropType} from 'vue'
import {filter, find, get, isEmpty, map, size} from 'lodash'
import {onMounted, ref} from 'vue'
import type {CanvasSite, Course} from '@/lib/types'
import {alertScreenReader, putFocusNextTick} from '@/lib/utils'
import {getCanvasSitesTeaching} from '@/api/user'
import {getCourseSite, updatePublishType} from '@/api/course'
import {useContextStore} from '@/stores/context'
import CanvasCourseSite from '@/components/course/CanvasCourseSite.vue'
import ProgressButton from '@/components/util/ProgressButton.vue'

type CanvasSiteOption = {
  id: string,
  disabled: boolean,
  role: string,
  title: string,
  value: CanvasSite
}

const props = defineProps({
  course: {
    required: true,
    type: Object as PropType<Course>
  },
  labels: {
    required: true,
    type: Object
  },
  setModel: {
    required: true,
    type: Function
  }
})

const {config, currentUser} = useContextStore()
const isEditing = ref(false)
const isFindingCanvasSite = ref(false)
const isSaving = ref(false)
const menuContainer = ref()
const pendingCanvasSite = ref()
const pendingCanvasSiteId = ref()
const publishCanvasSites = ref<CanvasSite[]>(props.course.canvasSites || [])
const publishCanvasSiteOptions = ref<CanvasSiteOption[]>([])
const publishType = ref(props.course.publishType)
const publishTypeOptions = Object.keys(config.publishTypeOptions).sort().reverse()

onMounted(() => {
  if (!currentUser.isAdmin && currentUser.uid) {
    getCanvasSitesTeaching(currentUser.uid).then(sites => {
      publishCanvasSiteOptions.value = map(sites, site => {
        return {
          id: `canvas-site-option-${site.canvasSiteId}`,
          disabled: isCanvasSiteIdStaged(site.canvasSiteId),
          role: 'option',
          title: `${site.name} (${site.courseCode})`,
          value: site
        }
      })
    })
  }
})

const addCanvasSiteById = () => {
  isFindingCanvasSite.value = true
  if (pendingCanvasSiteId.value && !isCanvasSiteIdStaged(pendingCanvasSiteId.value)) {
    getCourseSite(pendingCanvasSiteId.value).then(data => {
      if (data) {
        publishCanvasSites.value.push(data)
        isFindingCanvasSite.value = false
        pendingCanvasSiteId.value = null
        alertScreenReader(`${data.name} added.`)
        putFocusNextTick('input-canvas-site-id')
      }
    })
  }
}

const addCanvasSiteConfirm = () => {
  if (pendingCanvasSite.value && !isCanvasSiteIdStaged(pendingCanvasSite.value.canvasSiteId)) {
    publishCanvasSites.value.push(pendingCanvasSite.value)
    alertScreenReader(`Added course site ${pendingCanvasSite.value.name}.`)
  }
  putFocusNextTick('select-canvas-site')
  pendingCanvasSite.value = null
}

const isCanvasSiteIdStaged = (siteId) => {
  return !!find(publishCanvasSites.value, {'canvasSiteId': parseInt(siteId, 10)})
}

const onPublishTypeChange = (option, idx) => {
  publishType.value = publishType.value === option ? publishTypeOptions[idx - 1] : option
}

const onToggleCanvasSitesMenu = isOpen => {
  if (isOpen) {
    putFocusNextTick(get(publishCanvasSiteOptions.value, '0.id', 'canvas-site-list'))
  }
}

const removeCanvasSite = (canvasSiteId, index) => {
  const nextFocusIndex = (index + 1 === size(publishCanvasSites.value)) ? index - 1 : index + 1
  const nextFocusSiteId = get(publishCanvasSites.value, `${nextFocusIndex}.canvasSiteId`)
  const canvasSite = find(publishCanvasSites.value, c => c.canvasSiteId === canvasSiteId)
  const canvasSiteName = get(canvasSite, 'name', '')
  let nextFocusId = `btn-canvas-site-remove-${nextFocusSiteId}`
  publishCanvasSites.value = filter(publishCanvasSites.value, c => c.canvasSiteId !== canvasSiteId )
  alertScreenReader(`Removed course site ${canvasSiteName}.`)
  if (isEmpty(publishCanvasSites.value) || !nextFocusSiteId) {
    nextFocusId = currentUser.isAdmin ? 'input-canvas-site-id' : 'select-canvas-site'
  }
  putFocusNextTick(nextFocusId)
}

const toggleIsEditing = () => {
  isEditing.value = true
  putFocusNextTick('select-publish-type')
}

const updatePublishTypeClicked = () => {
  isSaving.value = true
  updatePublishType(
    publishCanvasSites.value.map(s => s.canvasSiteId),
    publishType.value,
    props.course.sectionId,
    props.course.termId
  ).then(course => {
    const message = `Recording placement updated to ${course.publishTypeName}.`
    alertScreenReader(message)
    putFocusNextTick('btn-publish-type-edit')
    props.setModel(course)
    isEditing.value = false
    isSaving.value = false
  })
}

const updatePublishTypeCancel = () => {
  alertScreenReader('Recording placement edit cancelled.')
  putFocusNextTick('btn-publish-type-edit')
  isEditing.value = false
  publishType.value = props.course.publishType
  publishCanvasSites.value = [...props.course.canvasSites]
}
</script>

<style scoped>
.canvas-site {
  height: fit-content !important;
  min-height: var(--v-chip-height) !important;
  width: fit-content;
}
</style>
