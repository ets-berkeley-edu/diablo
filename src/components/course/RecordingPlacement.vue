<template>
  <v-row
    align="center"
    aria-labelledby="publish-type-header"
    justify="start"
    role="region"
  >
    <v-col cols="12" class="px-4">
      <div :class="{'bg-surface-light border-sm pa-4 rounded w-100': isEditing}">
        <div v-if="!isEditing">
          <h3 id="publish-type-header">Recording Placement</h3>
          <div class="pl-4">
            <div id="publish-type-name" class="mt-2">
              {{ courseStore.displayLabels[course.publishType] }}
            </div>
            <v-btn
              id="btn-publish-type-edit"
              aria-label="Edit Recording Placement"
              class="elevation-1 mt-2"
              :disabled="courseStore.disableButtons"
              text="Edit"
              variant="outlined"
              @click="toggleIsEditing"
            />
          </div>
        </div>
        <div
          v-if="isEditing"
          id="select-publish-type"
          :aria-activedescendant="`radio-publish-type-${publishType}`"
          role="radiogroup"
          tabindex="0"
        >
          <h3 id="publish-type-header">
            <label for="select-publish-type">Recording Placement</label>
          </h3>
          <div
            v-for="(publishTypeOption, index) in publishTypeOptions"
            :key="publishTypeOption"
            class="d-flex flex-nowrap pl-4 pt-1"
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
            <label class="font-size-16 text-medium-emphasis" :for="`radio-publish-type-${publishTypeOption}`">{{ courseStore.displayLabels[publishTypeOption] }}</label>
          </div>
        </div>
        <div
          v-if="publishType && publishType.startsWith('kaltura_media_gallery') && (course.canvasSiteIds || isEditing)"
          id="publish-linked-canvas-site"
          class="mt-3 pl-4"
        >
          <h4 id="linked-course-sites-header">
            Linked bCourses <span :aria-hidden="true">site(s):</span><span class="sr-only">sites</span>
          </h4>
          <div v-if="!isEditing">
            <ul>
              <li v-for="canvasSite in course.canvasSites" :key="canvasSite.canvasSiteId">
                <CanvasCourseSite :course-site="canvasSite" :site-id="canvasSite.canvasSiteId" />
              </li>
            </ul>
          </div>
          <div v-if="isEditing">
            <div v-if="!currentUser.isAdmin" class="mt-1">
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
                variant="outlined"
                @update:menu="onToggleCanvasSitesMenu"
              >
                <template #item="{props: itemProps, item}">
                  <v-list-item
                    :id="`menu-option-canvas-site-${item.raw.canvasSiteId}`"
                    :disabled="item.raw.disabled"
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
            <div v-if="currentUser.isAdmin">
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
            <div class="d-flex flex-column">
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
                    class="ml-6"
                    color="warning"
                    :disabled="isSaving"
                    rounded
                    size="small"
                    text="Remove"
                    variant="flat"
                    @click="() => removeCanvasSite(site.canvasSiteId, index)"
                  />
                </template>
              </v-chip>
            </div>
            <div v-if="!currentUser.isAdmin" class="mt-2 text-body-2">
              To link a bCourses site from a past term, please <a :href="`mailto:${config.emailCourseCaptureSupport}`" target="_blank">contact Course Capture support.</a>
            </div>
          </div>
        </div>
        <div v-if="isEditing" class="mt-3 pl-4">
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
            class="ml-1"
            :disabled="isSaving"
            text="Cancel"
            variant="text"
            @click="updatePublishTypeCancel"
          />
        </div>
      </div>
    </v-col>
  </v-row>
</template>

<script lang="ts" setup>
import {each, filter, find, get, isEmpty, size} from 'lodash'
import {computed, onMounted, ref, watch} from 'vue'
import type {CanvasSite} from '@/lib/types'
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

const props = defineProps({
  setModel: {
    required: true,
    type: Function
  }
})

const {config, currentUser} = useContextStore()
const allCanvasSitesTeaching = ref<CanvasSite[]>([])
const courseStore = useCourseStore()
const course = courseStore.course
const isEditing = ref(false)
const isFindingCanvasSite = ref(false)
const isSaving = ref(false)
const menuContainer = ref()
const pendingCanvasSite = ref()
const pendingCanvasSiteId = ref()
const publishCanvasSites = ref<CanvasSite[]>(course.canvasSites || [])
const publishCanvasSiteOptions = computed((): CanvasSiteOption[] => {
  const options: CanvasSiteOption[] = []
  each(allCanvasSitesTeaching.value, site => {
    options.push({
      id: `canvas-site-option-${site.canvasSiteId}`,
      disabled: isCanvasSiteIdStaged(site.canvasSiteId),
      role: 'option',
      title: `${site.name} (${site.courseCode})`,
      value: site
    })
  })
  return options
})
const publishType = ref(course.publishType)
const publishTypeOptions = Object.keys(config.publishTypeOptions).sort().reverse()

watch(isEditing, courseStore.setDisableButtons)
watch(isSaving, courseStore.setDisableButtons)

onMounted(() => {
  if (!currentUser.isAdmin && currentUser.uid) {
    getCanvasSitesTeaching(currentUser.uid).then(data => {
      allCanvasSitesTeaching.value = data
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
    course.sectionId,
    course.termId
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
  publishType.value = course.publishType
  publishCanvasSites.value = [...course.canvasSites]
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
