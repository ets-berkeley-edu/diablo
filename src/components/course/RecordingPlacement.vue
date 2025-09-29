<template>
  <v-row
    align="center"
    aria-labelledby="publish-type-header"
    justify="start"
    no-gutters
    role="region"
  >
    <v-col cols="12">
      <div class="w-100">
        <h3 id="publish-type-header">
          <label for="select-publish-type">Recording Placement</label>
        </h3>
        <v-radio-group
          id="select-publish-type"
          v-model="publishType"
          :aria-activedescendant="`radio-publish-type-${publishType}`"
          class="mt-2"
          color="primary"
          density="comfortable"
          :disabled="courseStore.disableButtons"
          hide-details
        >
          <v-radio
            v-for="publishTypeOption in publishTypeOptions"
            :id="`radio-publish-type-${publishTypeOption}`"
            :key="publishTypeOption"
            :label="courseStore.displayLabels[publishTypeOption]"
            :value="publishTypeOption"
          />
        </v-radio-group>
        <v-expand-transition>
          <div
            v-if="publishType && publishType.startsWith('kaltura_media_gallery') && (currentUser.isAdmin || course.canvasSiteIds)"
            id="publish-linked-canvas-site"
            class="border-sm ma-3 pb-6 px-4 pt-4"
          >
            <h4 id="linked-course-sites-header">
              Linked bCourses site{{ course.canvasSites.length === 1 ? '' : 's' }}
            </h4>
            <div>
              <ul>
                <li v-for="canvasSite in course.canvasSites" :key="canvasSite.canvasSiteId">
                  <CanvasCourseSite :course-site="canvasSite" :site-id="canvasSite.canvasSiteId" />
                </li>
              </ul>
            </div>
            <div>
              <div v-if="!currentUser.isAdmin" class="mr-3 my-3">
                <v-select
                  id="select-canvas-site"
                  v-model="pendingCanvasSite"
                  aria-describedby="linked-course-sites-header"
                  aria-label="Select course site"
                  autocomplete="off"
                  density="compact"
                  :disabled="courseStore.disableButtons"
                  hide-details
                  item-props
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
                  :disabled="courseStore.disableButtons"
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
                  :class="{'mt-3': index === 0, 'mt-2': index > 0}"
                  class="canvas-site pl-4 pr-2 text-wrap"
                >
                  {{ site.name }} ({{ site.courseCode }})
                  <template #append>
                    <v-btn
                      :id="`btn-canvas-site-remove-${site.canvasSiteId}`"
                      :aria-label="`Remove ${site.name} (${site.courseCode})`"
                      class="ml-6"
                      color="warning"
                      :disabled="courseStore.disableButtons"
                      rounded
                      size="small"
                      text="Remove"
                      variant="flat"
                      @click="() => removeCanvasSite(site.canvasSiteId, index)"
                    />
                  </template>
                </v-chip>
              </div>
              <div v-if="!currentUser.isAdmin" class="font-italic ml-1 mt-2 text-body-2">
                <span class="font-weight-bold">Note:</span> To link a bCourses site from a past term,
                please <a :href="`mailto:${config.emailCourseCaptureSupport}`" target="_blank">contact Course Capture support.</a>
              </div>
            </div>
          </div>
        </v-expand-transition>
      </div>
    </v-col>
  </v-row>
</template>

<script lang="ts" setup>
import {each, filter, find, get, isEmpty, size} from 'lodash'
import {onMounted, ref} from 'vue'
import {storeToRefs} from 'pinia'
import type {CanvasSite} from '@/lib/types'
import {alertScreenReader, putFocusNextTick} from '@/lib/utils'
import {getCanvasSitesTeaching} from '@/api/user'
import {getCourseSite} from '@/api/course'
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

const publishType = defineModel('publishType',{required: true, type: String})
const canvasSiteIds = defineModel('canvasSiteIds',{required: true, type: Array<number>})

const courseStore = useCourseStore()
const {config, currentUser} = useContextStore()
const {course} = storeToRefs(courseStore)
const canvasSiteOptions = ref<CanvasSiteOption[]>([])
const isFindingCanvasSite = ref(false)
const menuContainer = ref()
const pendingCanvasSite = ref()
const pendingCanvasSiteId = ref<number | undefined>()
const publishCanvasSites = ref<CanvasSite[]>(course.canvasSites || [])
const publishTypeOptions = Object.keys(config.publishTypeOptions).sort().reverse()

onMounted(() => {
  if (!currentUser.isAdmin && currentUser.uid) {
    getCanvasSitesTeaching(currentUser.uid).then(data => {
      each(data, site => {
        canvasSiteOptions.value.push({
          id: `canvas-site-option-${site.canvasSiteId}`,
          disabled: isCanvasSiteIdStaged(site.canvasSiteId),
          role: 'option',
          title: `${site.name} (${site.courseCode})`,
          value: site
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
        canvasSiteIds.value.push(data.canvasSiteId)
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
    publishCanvasSites.value.push(canvasSiteId)
    alertScreenReader(`Added course site ${pendingCanvasSite.value.name}.`)
  }
  putFocusNextTick('select-canvas-site')
  pendingCanvasSite.value = null
}

const isCanvasSiteIdStaged = (siteId) => {
  return !!find(publishCanvasSites.value, {'canvasSiteId': parseInt(siteId, 10)})
}

const onToggleCanvasSitesMenu = isOpen => {
  if (isOpen) {
    putFocusNextTick(get(canvasSiteOptions.value, '0.id', 'canvas-site-list'))
  }
}

const removeCanvasSite = (canvasSiteId, index) => {
  const nextFocusIndex = (index + 1 === size(publishCanvasSites.value)) ? index - 1 : index + 1
  const nextFocusSiteId = get(publishCanvasSites.value, `${nextFocusIndex}.canvasSiteId`)
  const canvasSite = find(publishCanvasSites.value, c => c.canvasSiteId === canvasSiteId)
  const canvasSiteName = get(canvasSite, 'name', '')
  let nextFocusId = `btn-canvas-site-remove-${nextFocusSiteId}`
  publishCanvasSites.value = filter(publishCanvasSites.value, c => c.canvasSiteId !== canvasSiteId)
  canvasSiteIds.value = filter(canvasSiteIds.value, id => id !== canvasSiteId )
  alertScreenReader(`Removed course site ${canvasSiteName}.`)
  if (isEmpty(publishCanvasSites.value) || !nextFocusSiteId) {
    nextFocusId = currentUser.isAdmin ? 'input-canvas-site-id' : 'select-canvas-site'
  }
  putFocusNextTick(nextFocusId)
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
