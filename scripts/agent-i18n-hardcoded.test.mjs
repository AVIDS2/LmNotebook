import test from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'

async function readText(path) {
  return readFile(new URL(`../${path}`, import.meta.url), 'utf8')
}

test('session/model/agent key labels should use i18n keys instead of selected hardcoded strings', async () => {
  const sessionHistory = await readText('src/renderer/src/components/agent/SessionHistoryPanel.vue')
  const modelSettings = await readText('src/renderer/src/components/agent/ModelSettings.vue')
  const agentBubble = await readText('src/renderer/src/components/agent/AgentBubble.vue')

  const forbiddenSessionTokens = ['取消置顶', '置顶', '重命名', '删除']
  for (const token of forbiddenSessionTokens) {
    assert.ok(!sessionHistory.includes(token), `SessionHistoryPanel still contains hardcoded token: ${token}`)
  }

  const forbiddenModelTokens = [
    '模型设置',
    '配置 AI 服务提供商',
    '添加提供商',
    '设为活动',
    '提供商名称',
    '默认模型（活动模型）',
    '请选择或添加一个提供商',
    '确定要删除此提供商吗？'
  ]
  for (const token of forbiddenModelTokens) {
    assert.ok(!modelSettings.includes(token), `ModelSettings still contains hardcoded token: ${token}`)
  }

  const forbiddenAgentTokens = [
    'Ask, search, or make anything...',
    '提问、搜索或执行任务...',
    'Upload image',
    '上传图片',
    'Upload file',
    '上传文件',
    'Knowledge base',
    'Add note context',
    '添加笔记上下文',
    'Select note',
    '选择笔记',
    'No notes',
    '暂无笔记',
    'Choose model',
    '选择模型',
    'Allow write action?',
    '允许执行写入操作？',
    'Allow once',
    '接受一次',
    "copyItem.textContent = '复制'"
  ]
  for (const token of forbiddenAgentTokens) {
    assert.ok(!agentBubble.includes(token), `AgentBubble still contains hardcoded token: ${token}`)
  }
})
