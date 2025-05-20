<template>
  <div v-if="editor">
    <div class="bg-secondary pa-1 rounded-t-sm">
      <v-btn
        v-for="button in toolbarButtons"
        :id="`${idPrefix}-editor-toolbar-btn-${button.key}`"
        :key="button.key"
        :active="button.isActive ? button.isActive() : editor.isActive(button.key)"
        :aria-pressed="button.isActive ? button.isActive() : editor.isActive(button.key)"
        class="ma-1"
        :icon="button.icon"
        size="30"
        :title="button.label"
        variant="text"
        @click="button.onClick"
      />
      <v-dialog
        v-model="linkDialog"
        :aria-labelledby="`${idPrefix}-link-dialog-header`"
        max-width="600"
        min-width="400"
        persistent
        role="dialog"
        width="50%"
        @after-enter="() => putFocusNextTick(`${props.idPrefix}-link-url-input`)"
        @after-leave="onCloseLinkDialog"
      >
        <v-card class="modal-content">
          <v-card-title>
            <h2 :id="`${idPrefix}-link-dialog-header`">Create a Link</h2>
          </v-card-title>
          <v-card-text class="py-1">
            <v-text-field
              :id="`${idPrefix}-link-url-input`"
              v-model="linkUrl"
              label="URL"
            ></v-text-field>
          </v-card-text>
          <v-card-actions>
            <v-btn
              :id="`${idPrefix}-link-url-btn-apply`"
              color="primary"
              density="comfortable"
              text="Apply"
              variant="flat"
              @click="createLink"
            />
            <v-btn
              :id="`${idPrefix}-link-url-btn-cancel`"
              density="comfortable"
              text="Cancel"
              variant="text"
              @click="() => linkDialog = false"
            />
          </v-card-actions>
        </v-card>
      </v-dialog>
    </div>
    <EditorContent
      :id="`${idPrefix}-editor-content`"
      class="editor-content bg-surface pa-4"
      :editor="editor"
    />
  </div>
</template>

<script setup>
import {defineEmits, defineProps, onBeforeUnmount, ref} from 'vue'
import Link from '@tiptap/extension-link'
import {
  mdiCodeTags,
  mdiFormatBold,
  mdiFormatHeader1,
  mdiFormatHeader2,
  mdiFormatHeader3,
  mdiFormatItalic,
  mdiFormatListBulleted,
  mdiFormatListNumbered,
  mdiFormatPilcrowArrowRight,
  mdiFormatQuoteClose,
  mdiFormatStrikethrough,
  mdiFormatUnderline,
  mdiLink,
  mdiMinus,
  mdiRedo,
  mdiUndo
} from '@mdi/js'
import Placeholder from '@tiptap/extension-placeholder'
import StarterKit from '@tiptap/starter-kit'
import Underline from '@tiptap/extension-underline'
import {useEditor, EditorContent} from '@tiptap/vue-3'
import {putFocusNextTick} from '@/lib/utils'

const props = defineProps({
  idPrefix: {
    default: 'text',
    required: false,
    type: String
  },
  modelValue: {
    default: '',
    type: String
  },
  placeholder: {
    default: '',
    type: String
  }
})

const emit = defineEmits(['update:modelValue'])

const editor = useEditor({
  content: props.modelValue,
  extensions: [
    Link,
    Placeholder.configure({
      emptyEditorClass: 'editor-empty',
      placeholder: props.placeholder
    }),
    StarterKit.configure({
      heading: {
        levels: [1, 2, 3]
      }
    }),
    Underline
  ],
  onUpdate: ({editor: currentEditor}) => {
    emit('update:modelValue', currentEditor.getHTML())
  }
})
const linkDialog = ref(false)
const linkUrl = ref('')
const toolbarButtons = [
  {
    key: 'undo',
    label: 'Undo',
    icon: mdiUndo,
    onClick: () => editor.value.chain().focus().undo().run()
  },
  {
    key: 'redo',
    label: 'Redo',
    icon: mdiRedo,
    onClick: () => editor.value.chain().focus().redo().run()
  },
  {
    key: 'blockquote',
    label: 'Block quote',
    icon: mdiFormatQuoteClose,
    onClick: () => editor.value.chain().focus().toggleBlockquote().run()
  },
  {
    key: 'link',
    label: 'Add link',
    icon: mdiLink,
    onClick: () => {
      if (editor.value.isActive('link')) {
        editor.value.chain().focus().unsetLink().run()
      } else {
        linkDialog.value = true
      }
    }
  },
  {
    key: 'bold',
    label: 'Bold',
    icon: mdiFormatBold,
    onClick: () => editor.value.chain().focus().toggleBold().run()
  },
  {
    key: 'underline',
    label: 'Underline',
    icon: mdiFormatUnderline,
    onClick: () => editor.value.chain().focus().toggleUnderline().run()
  },
  {
    key: 'strike',
    label: 'Strike',
    icon: mdiFormatStrikethrough,
    onClick: () => editor.value.chain().focus().toggleStrike().run()
  },
  {
    key: 'italic',
    label: 'Italic',
    icon: mdiFormatItalic,
    onClick: () => editor.value.chain().focus().toggleItalic().run()
  },
  {
    key: 'bulletList',
    label: 'Bulleted list',
    icon: mdiFormatListBulleted,
    onClick: () => editor.value.chain().focus().toggleBulletList().run()
  },
  {
    key: 'orderedList',
    label: 'Ordered list',
    icon: mdiFormatListNumbered,
    onClick: () => editor.value.chain().focus().toggleOrderedList().run()
  },
  {
    key: 'heading1',
    label: 'Level 1 header',
    icon: mdiFormatHeader1,
    isActive: () => editor.value.isActive('heading', {level: 1}),
    onClick: () => editor.value.chain().focus().toggleHeading({level: 1}).run()
  },
  {
    key: 'heading2',
    label: 'Level 2 header',
    icon: mdiFormatHeader2,
    isActive: () => editor.value.isActive('heading', {level: 2}),
    onClick: () => editor.value.chain().focus().toggleHeading({level: 2}).run()
  },
  {
    key: 'heading3',
    label: 'Level 3 header',
    icon: mdiFormatHeader3,
    isActive: () => editor.value.isActive('heading', {level: 3}),
    onClick: () => editor.value.chain().focus().toggleHeading({level: 3}).run()
  },
  {
    key: 'code',
    label: 'Code',
    icon: mdiCodeTags,
    onClick: () => editor.value.chain().focus().toggleCode().run()
  },
  {
    key: 'horizontalRule',
    label: 'Horizontal line',
    icon: mdiMinus,
    onClick: () => editor.value.chain().focus().setHorizontalRule().run()
  },
  {
    key: 'paragraph',
    label: 'Paragraph',
    icon: mdiFormatPilcrowArrowRight,
    onClick: () => editor.value.chain().focus().setParagraph().run()
  },
]

onBeforeUnmount(() => {
  editor.value.destroy()
})

const createLink = () => {
  editor.value.chain().focus().extendMarkRange('link').setLink({href: linkUrl.value}).run()
  linkDialog.value = false
}

const onCloseLinkDialog = () => {
  linkUrl.value = ''
  putFocusNextTick(`${props.idPrefix}-editor-toolbar-btn-link`)
}
</script>

<style>
.editor-content .tiptap {
  min-height: 2.125rem;
  padding: 5px;
}
.editor-content .tiptap ul,
.editor-content .tiptap ol {
  padding: 0 1rem;
  margin: 1rem 0.4rem;
}
.editor-content .tiptap ul li p,
.editor-content .tiptap ol li p {
  margin: 0.25em 0;
}
.editor-content .tiptap p.editor-empty:first-child::before {
  color: rgba(var(--v-theme-on-surface), var(--v-medium-emphasis-opacity));
  content: attr(data-placeholder);
  float: left;
  font-style: italic;
  height: 0;
  pointer-events: none;
}
</style>
