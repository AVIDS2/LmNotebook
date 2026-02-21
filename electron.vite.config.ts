import { resolve } from 'path'
import { defineConfig, externalizeDepsPlugin } from 'electron-vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  main: {
    plugins: [externalizeDepsPlugin()]
  },
  preload: {
    plugins: [externalizeDepsPlugin()]
  },
  renderer: {
    resolve: {
      alias: {
        '@': resolve('src/renderer/src')
      }
    },
    build: {
      rollupOptions: {
        output: {
          manualChunks(id) {
            if (!id.includes('node_modules')) return
            if (id.includes('mammoth')) return 'vendor-mammoth'
            if (id.includes('@tiptap') || id.includes('prosemirror')) return 'vendor-editor'
            if (id.includes('katex') || id.includes('highlight.js') || id.includes('lowlight')) return 'vendor-richtext'
            if (id.includes('marked') || id.includes('dompurify') || id.includes('tiptap-markdown')) return 'vendor-markdown'
          }
        }
      }
    },
    plugins: [vue()],
    css: {
      preprocessorOptions: {
        scss: {
          additionalData: `@use "@/assets/styles/variables" as *;`,
          api: 'modern-compiler'
        }
      }
    }
  }
})
