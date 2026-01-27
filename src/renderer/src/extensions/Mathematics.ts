import { Node, mergeAttributes } from '@tiptap/core'
import katex from 'katex'

declare module '@tiptap/core' {
    interface Commands<ReturnType> {
        math: {
            insertMath: (latex?: string) => ReturnType
        }
    }
}

// LaTeX 公式扩展 - 简化版
export const Mathematics = Node.create({
    name: 'math',
    group: 'inline',
    inline: true,
    atom: true,
    selectable: true,
    draggable: true,

    addAttributes() {
        return {
            latex: {
                default: '',
            }
        }
    },

    parseHTML() {
        return [
            {
                tag: 'span[data-math]',
                getAttrs: (node) => {
                    if (typeof node === 'string') return {}
                    return {
                        latex: node.getAttribute('data-latex') || ''
                    }
                }
            }
        ]
    },

    renderHTML({ HTMLAttributes }) {
        const latex = HTMLAttributes.latex || ''
        let rendered = latex

        try {
            rendered = katex.renderToString(latex, {
                throwOnError: false,
                displayMode: false
            })
        } catch {
            rendered = `<span class="math-error">${latex}</span>`
        }

        return ['span', mergeAttributes({
            'data-math': '',
            'data-latex': latex,
            class: 'math-node',
            contenteditable: 'false'
        }), ['span', { innerHTML: rendered }]]
    },

    addNodeView() {
        return ({ node }) => {
            const dom = document.createElement('span')
            dom.className = 'math-node'
            dom.contentEditable = 'false'
            dom.setAttribute('data-math', '')
            dom.setAttribute('data-latex', node.attrs.latex || '')

            const latex = node.attrs.latex || ''

            if (!latex.trim()) {
                dom.innerHTML = '<span class="math-placeholder">$公式$</span>'
            } else {
                try {
                    katex.render(latex, dom, {
                        throwOnError: false,
                        displayMode: false
                    })
                } catch {
                    dom.innerHTML = `<span class="math-error">${latex}</span>`
                }
            }

            // 双击编辑
            dom.addEventListener('dblclick', () => {
                const newLatex = prompt('编辑 LaTeX 公式:', latex)
                if (newLatex !== null) {
                    dom.setAttribute('data-latex', newLatex)
                    if (!newLatex.trim()) {
                        dom.innerHTML = '<span class="math-placeholder">$公式$</span>'
                    } else {
                        try {
                            katex.render(newLatex, dom, {
                                throwOnError: false,
                                displayMode: false
                            })
                        } catch {
                            dom.innerHTML = `<span class="math-error">${newLatex}</span>`
                        }
                    }
                }
            })

            return { dom }
        }
    },

    addCommands() {
        return {
            insertMath: (latex = '') => ({ commands }) => {
                return commands.insertContent({
                    type: 'math',
                    attrs: { latex }
                })
            }
        }
    },

    // 支持输入规则: $...$
    addInputRules() {
        return []
    }
})

export default Mathematics
