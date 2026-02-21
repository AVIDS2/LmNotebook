#!/usr/bin/env node
import { spawnSync } from 'node:child_process'
import { existsSync } from 'node:fs'
import { resolve } from 'node:path'

const repoRoot = process.cwd()

function run(label, command, args) {
  console.log(`\n[run] ${label}`)
  const result = spawnSync(command, args, {
    cwd: repoRoot,
    stdio: 'inherit',
    shell: process.platform === 'win32'
  })
  return result.status === 0
}

function checkPath(label, relativePath, required = true) {
  const ok = existsSync(resolve(repoRoot, relativePath))
  const tag = ok ? 'OK' : required ? 'FAIL' : 'WARN'
  console.log(`[${tag}] ${label}: ${relativePath}`)
  return { ok, required }
}

console.log('Release Readiness Checklist')
console.log('===========================')

const staticChecks = [
  checkPath('Windows icon (.ico)', 'build/icon.ico', true),
  checkPath('App icon (.png)', 'build/icon.png', true),
  checkPath('Backend dist', 'src/backend/dist/origin_backend', false),
  checkPath('Backend env file', 'src/backend/.env', false)
]

const testsOk = run('UI hardening contract tests', 'node', ['scripts/ui-hardening-contract.test.mjs'])
const buildOk = run('Renderer/Main production build', 'npm', ['run', 'build'])

const requiredOk = staticChecks.filter((x) => x.required).every((x) => x.ok)
const allOk = requiredOk && testsOk && buildOk

console.log('\nSummary')
console.log('-------')
console.log(`Required static checks: ${requiredOk ? 'PASS' : 'FAIL'}`)
console.log(`UI contract tests: ${testsOk ? 'PASS' : 'FAIL'}`)
console.log(`Production build: ${buildOk ? 'PASS' : 'FAIL'}`)

if (!allOk) {
  process.exitCode = 1
}
