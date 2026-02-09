<template>
  <div class="markdown-renderer">
    <div ref="renderedContent" v-html="renderedContent" class="rendered-content" :data-original-markdown="originalMarkdown"></div>
  </div>
</template>

<script>
import { marked } from 'marked';
import DOMPurify from 'dompurify';
import katex from 'katex';
import Prism from 'prismjs';

import 'prismjs/components/prism-markup-templating'; 
// 导入 Prism 的其他语言支持
import 'prismjs/components/prism-python';
import 'prismjs/components/prism-java';
import 'prismjs/components/prism-javascript';
import 'prismjs/components/prism-css';
import 'prismjs/components/prism-markup';
import 'prismjs/components/prism-c'; 
import 'prismjs/components/prism-cpp';
import 'prismjs/components/prism-go';
import 'prismjs/components/prism-bash';
import 'prismjs/components/prism-json';
import 'prismjs/components/prism-yaml';
import 'prismjs/components/prism-typescript';
import 'prismjs/components/prism-sql';
import 'prismjs/components/prism-rust';
import 'prismjs/components/prism-csharp';
// ... 其他导入 ...

export default {
  name: 'MarkdownRenderer',

  props: {
    content: {
      type: String,
      required: true
    }
  },

  data() {
    return {
      renderedContent: '',
      mathFormulas: [], // 存储所有公式信息 (行内+块级)
      originalMarkdown: '', // 存储原始 Markdown 文本，用于复制功能
    };
  },

  watch: {
    content: {
      immediate: true,
      handler(newContent) {
        this.renderMarkdown(newContent);
      }
    }
  },

  created() {
    // 设置 marked 选项 (移除 highlight)
    marked.setOptions({
      gfm: true,
      breaks: true,
      headerIds: true,
      headerPrefix: 'heading-',
      mangle: false,
    });
  },

  beforeDestroy() {
  },

  methods: {
    extractAndProcessMath(markdownText) {
      const formulas = [];
      let processedText = markdownText;
      let counter = 0;

      // 1. 处理块级公式 ($$ ... $$)
      processedText = processedText.replace(/\$\$([\s\S]+?)\$\$/g, (match, formula) => {
        const id = `math-placeholder-${counter++}`;
        formulas.push({ id, formula: formula.trim(), displayMode: true });
        return `<span class="katex-placeholder" data-id="${id}"></span>`;
      });

      // 2. 处理行内公式 ($ ... $)
      processedText = processedText.replace(/(^|[^\\])\$([^\$\n\r]+?)\$/g, (match, prefix, formula) => {
        // 避免将 $1.23$ 这样的内容识别为公式
        if (/^\s*\d+(\.\d+)?\s*$/.test(formula)) {
          return match;
        }
        const id = `math-placeholder-${counter++}`;
        formulas.push({ id, formula: formula.trim(), displayMode: false });
        return `${prefix}<span class="katex-placeholder" data-id="${id}"></span>`;
      });

      // 处理转义的 $ 符号
      processedText = processedText.replace(/\\<span class="katex-placeholder"/g, '$<span class="katex-placeholder"');

      this.mathFormulas = formulas;
      return processedText;
    },

    processAllPlaceholders() {
      if (!this.$refs.renderedContent) return;

      const placeholders = this.$refs.renderedContent.querySelectorAll('.katex-placeholder');
      placeholders.forEach(placeholder => {
        const id = placeholder.getAttribute('data-id');
        const mathInfo = this.mathFormulas.find(f => f.id === id);

        if (mathInfo) {
          try {
            katex.render(mathInfo.formula, placeholder, {
              displayMode: mathInfo.displayMode,
              throwOnError: false,
              strict: false,
              trust: true
            });
            placeholder.classList.add(mathInfo.displayMode ? 'katex-display-block' : 'katex-inline-block');
            placeholder.setAttribute('data-formula', mathInfo.formula);
          } catch (e) {
            console.error(`KaTeX 渲染错误 (ID ${id}):`, e);
            placeholder.textContent = `[KaTeX Error]`;
            placeholder.style.color = 'red';
          }
        } else {
          console.warn(`未找到 ID 为 ${id} 的数学公式数据`);
          placeholder.textContent = `[Math Data Missing]`;
        }
      });
    },

    processCustomElements(text) {
      // 处理高亮文本 ==...==
      text = text.replace(/==([^=<>]+?)==/g, '<mark>$1</mark>');
      // 处理上标 ^...^ (确保不在 HTML 标签内)
      text = text.replace(/([^\^])\^([^\^<>]+?)\^/g, '$1<sup>$2</sup>');
      // 处理下标 ~...~ (确保不在 HTML 标签内)
      text = text.replace(/([^~])~([^~<>]+?)~/g, '$1<sub>$2</sub>');
      return text;
    },

    highlightCodeInContent() {
      if (!this.$refs.renderedContent) return;
      try {
        const codeElements = this.$refs.renderedContent.querySelectorAll('pre code');
        codeElements.forEach((block) => {
          // 检查语言是否存在，如果不存在，Prism 会自动处理
          const langClass = Array.from(block.classList).find(cls => cls.startsWith('language-'));
          if (langClass) {
            const lang = langClass.replace('language-', '');
            if (Prism.languages[lang]) {
              Prism.highlightElement(block);
            } else {
              console.warn(`Prism language '${lang}' not loaded for block:`, block.textContent.substring(0, 50) + '...');
              // 可以选择添加一个默认类或不做处理
              block.classList.add('language-plaintext'); // 明确标记为纯文本
            }
          } else {
             // 没有指定语言，标记为纯文本
             block.classList.add('language-plaintext');
          }
        });
      } catch (error) {
        console.error('Prism 高亮错误:', error);
      }
    },

    initializeCodeBlocks() {
      try {
        const codeBlocks = this.$refs.renderedContent.querySelectorAll('pre code');

        codeBlocks.forEach((block) => {
          // 检查是否已经被包装过
          if (block.closest('.code-block')) return;

          const languageClass = Array.from(block.classList)
            .find(className => className.startsWith('language-'));
          const language = languageClass ? languageClass.replace('language-', '') : 'plaintext';

          const codeBlockWrapper = document.createElement('div');
          codeBlockWrapper.className = 'code-block';

          const header = document.createElement('div');
          header.className = 'code-header';
          header.innerHTML = `
            <span class="code-language">${language}</span>
            <button class="copy-button" title="复制代码">复制代码</button>
          `;

          const copyButton = header.querySelector('.copy-button');
          copyButton.addEventListener('click', () => {
            const code = block.textContent;
            navigator.clipboard.writeText(code).then(() => {
              copyButton.textContent = '已复制！';
              setTimeout(() => {
                copyButton.textContent = '复制代码';
              }, 2000);
            }).catch(err => {
              console.error('复制失败:', err);
              copyButton.textContent = '复制失败';
              setTimeout(() => {
                copyButton.textContent = '复制代码';
              }, 2000);
            });
          });

          const preElement = block.parentElement;
          // 确保 preElement 存在且有父节点
          if (preElement && preElement.parentNode) {
              preElement.parentNode.insertBefore(codeBlockWrapper, preElement);
              codeBlockWrapper.appendChild(header);
              codeBlockWrapper.appendChild(preElement);
              // Prism.highlightElement(block); // <--- 再次移除或注释掉这一行
          } else {
              console.warn('无法包装代码块，父元素不存在:', block);
          }
        });
      } catch (error) {
        console.error('代码块初始化错误:', error);
      }
    },

    async postRenderProcessing() {
      if (this.$refs.renderedContent) {
        this.processAllPlaceholders(); // 1. 处理 KaTeX
        this.initializeCodeBlocks();   // 2. 初始化代码块（添加头部/包装器）
        this.highlightCodeInContent(); // 3. 调用 Prism 高亮
      }
    },

    renderMarkdown(markdown) {
      try {
        if (!markdown) {
          this.renderedContent = '';
          this.originalMarkdown = '';
          this.mathFormulas = [];
          return;
        }

        const markdownStr = String(markdown);
        this.originalMarkdown = markdownStr; // 存储原始 Markdown

        // 1. 提取并替换数学公式占位符
        const processedMarkdown = this.extractAndProcessMath(markdownStr);

        // 2. 使用 marked 解析 Markdown (Mermaid 代码块会被保留)
        let html = marked.parse(processedMarkdown);

        // 3. 应用自定义元素处理（如 <mark>, <sup>, <sub>）
        html = this.processCustomElements(html);

        // 4. 使用 DOMPurify 清理 HTML
        html = DOMPurify.sanitize(html, {
          ADD_TAGS: ['math', 'mtext', 'annotation', 'semantics', 'svg', 'mark', 'sub', 'sup', 'span', 'em', 'strong', 'div', 'pre', 'code'],
          ADD_ATTR: ['xmlns', 'display', 'dir', 'style', 'viewBox', 'width', 'height', 'id', 'class', 'data-code', 'data-original-markdown', 'aria-label', 'data-id', 'data-formula'],
          FORBID_TAGS: ['script', 'iframe'], // 禁止危险标签
          FORBID_ATTR: ['onerror', 'onload'], // 禁止危险属性
          USE_PROFILES: { html: true },
          ALLOW_DATA_ATTR: true, // 允许 data-* 属性
        });

        this.renderedContent = html;

        // 5. 在 DOM 更新后，异步处理占位符（KaTeX）、代码块和 Mermaid 图表
        this.$nextTick(() => {
          this.postRenderProcessing();
        });

      } catch (error) {
        console.error('Markdown渲染错误:', error);
        this.renderedContent = `<p class="error-message">渲染错误: ${error.message}</p>`;
        this.originalMarkdown = ''; // 清空原始 Markdown
        this.mathFormulas = []; // 清空公式
      }
    },
  }
};
</script>

<style>
/* ... (保留现有样式) ... */
@import 'katex/dist/katex.min.css';
@import 'prismjs/themes/prism.css';

/* KaTeX 相关样式 */
.katex-placeholder {
  display: inline-block; /* 默认行内块 */
  min-width: 1em; /* 避免空占位符塌陷 */
  min-height: 1em;
}

.katex-display-block {
  display: block; /* 块级公式 */
  text-align: center; /* 块级公式居中 */
  margin: 1em 0;
  overflow-x: auto;
  padding: 0.5em 0;
}

.katex-inline-block {
  display: inline-block; /* 行内公式 */
  vertical-align: middle; /* 尝试垂直对齐 */
}

/* 调整 .katex-display 样式（如果 KaTeX 内部生成了这个类） */
.katex-display {
  overflow-x: auto;
  overflow-y: hidden;
  padding: 1em 0;
  margin: 0.5em 0;
}

.katex {
  font-size: 1.1em;
}

/* ... (保留其他样式) ... */

.markdown-renderer {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
  line-height: 1.6;
  color: #333;
  text-align: left;
  width: 100%;
  display: inline-block; /* 或者 block，根据布局需要 */
}

/* 代码块样式 */
.code-block {
  margin: 1em 0;
  border-radius: 6px;
  overflow: hidden;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
  position: relative; /* 为了头部定位 */
}

.code-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5em 1em;
  background: #2d2d2d; /* 深色背景 */
  color: #ccc; /* 浅色文字 */
  font-size: 0.9em;
}

.code-language {
  text-transform: uppercase;
  font-size: 0.8em;
  font-weight: bold;
  color: #eee;
}

.copy-button {
  background: #444;
  border: none;
  color: #fff;
  padding: 0.3em 0.8em;
  border-radius: 3px;
  cursor: pointer;
  font-size: 0.8em;
  transition: background 0.2s, color 0.2s;
}

.copy-button:hover {
  background: #666;
}

/* Prism 代码高亮基础样式调整 */
.markdown-renderer pre[class*="language-"] {
  margin: 0; /* 移除 pre 的外边距，由 .code-block 控制 */
  border-radius: 0 0 6px 6px; /* 调整圆角 */
  background-color: #f5f5f5; /* 浅色代码背景 */
  border: none; /* 移除边框 */
  padding: 1em; /* 内边距 */
  overflow: auto;
}

.markdown-renderer code[class*="language-"] {
  font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
  color: #333; /* 代码颜色 */
  background: none; /* 移除 code 的背景 */
  padding: 0; /* 移除 code 的内边距 */
  font-size: 0.9em; /* 调整字体大小 */
  text-shadow: none; /* 移除文本阴影 */
}

/* 错误消息样式 */
.error-message {
  color: #dc3545; /* 红色 */
  padding: 1em;
  background: #f8d7da; /* 淡红色背景 */
  border: 1px solid #f5c6cb; /* 红色边框 */
  border-left: 4px solid #dc3545; /* 左侧加粗边框 */
  margin: 1em 0;
  border-radius: 4px;
}

/* 高亮文本样式 */
mark {
  background-color: #fff3cd; /* 黄色背景 */
  padding: 0.2em;
  border-radius: 2px;
}

.rendered-content {
  min-width: auto;
  width: auto; /* 或者 100% */
  display: inline-block; /* 或者 block */
}

.simple-text {
  margin: 0;
  padding: 0;
  white-space: pre-wrap; /* 保留空格和换行 */
  word-break: break-word; /* 单词换行 */
}

/* 标题样式 */
.markdown-renderer h1,
.markdown-renderer h2,
.markdown-renderer h3,
.markdown-renderer h4,
.markdown-renderer h5,
.markdown-renderer h6 {
  margin-top: 1.5em;
  margin-bottom: 0.5em;
  font-weight: 600;
  line-height: 1.25;
  text-align: left;
}

.markdown-renderer h1 { font-size: 2em; border-bottom: 1px solid #eee; padding-bottom: 0.3em; }
.markdown-renderer h2 { font-size: 1.5em; border-bottom: 1px solid #eee; padding-bottom: 0.3em; }
.markdown-renderer h3 { font-size: 1.3em; }
.markdown-renderer h4 { font-size: 1.1em; }
.markdown-renderer h5 { font-size: 1em; }
.markdown-renderer h6 { font-size: 0.9em; color: #777; }

.markdown-renderer .code-block > pre {
  margin: 0; /* 移除 pre 的外边距，由 .code-block 控制 */
  border-radius: 0 0 6px 6px; /* 调整圆角 */
  background-color: #f5f5f5; /* 浅色代码背景 */
  border: none; /* 移除边框 */
  padding: 1em; /* 内边距 */
  overflow: auto;
}

/* 移除代码块内 code 的背景和内边距 */
.markdown-renderer pre > code {
  background-color: transparent;
  padding: 0;
  margin: 0;
  font-size: inherit; /* 继承 pre 的字体大小 */
  border-radius: 0;
  border: 0;
}

/* 引用块样式 */
.markdown-renderer blockquote {
  padding: 0 1em;
  color: #57606a;
  border-left: 0.25em solid #d0d7de;
  margin: 0 0 16px 0;
}
.markdown-renderer blockquote p {
  margin-top: 0;
  margin-bottom: 0;
}

/* 段落样式 */
.markdown-renderer p {
  margin-top: 0;
  margin-bottom: 1em; /* 段落下边距 */
  text-align: left;
}

/* 列表样式 */
.markdown-renderer ul,
.markdown-renderer ol {
  text-align: left;
  padding-left: 2em;
  margin-top: 0;
  margin-bottom: 1em;
}
.markdown-renderer ul li,
.markdown-renderer ol li {
  margin-bottom: 0.25em;
}

/* 表格样式 */
.markdown-renderer table {
  border-collapse: collapse;
  margin: 1em 0;
  display: block; /* 允许水平滚动 */
  width: max-content; /* 表格内容决定宽度 */
  max-width: 100%; /* 不超过容器宽度 */
  overflow: auto;
  text-align: left;
  border-spacing: 0;
}

.markdown-renderer table th,
.markdown-renderer table td {
  border: 1px solid #dfe2e5;
  padding: 6px 13px;
}

.markdown-renderer table th {
  font-weight: 600;
  background-color: #f6f8fa;
}

.markdown-renderer table tr {
  background-color: #fff;
  border-top: 1px solid #c6cbd1;
}

.markdown-renderer table tr:nth-child(2n) {
  background-color: #f6f8fa;
}

/* 图片样式 */
.markdown-renderer img {
  max-width: 100%;
  box-sizing: content-box;
  background-color: #fff;
}

/* 分隔线样式 */
.markdown-renderer hr {
  height: 0.25em; /* 加粗分隔线 */
  padding: 0;
  margin: 24px 0;
  background-color: #e1e4e8;
  border: 0;
}
</style>