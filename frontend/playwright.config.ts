import { readFileSync } from 'node:fs'
import path from 'node:path'
import process from 'node:process'
import { fileURLToPath } from 'node:url'

import { defineConfig, devices } from '@playwright/test'

const rootDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')

/** Логин суперюзера задаётся в корневом .env — тому же файлу верит и compose.
 *  Читаем его сами, чтобы не тащить dotenv ради четырёх строк. */
function readRootEnv(key: string, fallback: string): string {
  const fromProcess = process.env[key]
  if (fromProcess) return fromProcess
  try {
    const line = readFileSync(path.join(rootDir, '.env'), 'utf8')
      .split('\n')
      .find((row) => row.startsWith(`${key}=`))
    return line ? line.slice(key.length + 1).trim() : fallback
  } catch {
    return fallback
  }
}

export const E2E = {
  login: readRootEnv('AUTH_SUPERUSER_LOGIN', 'admin'),
  password: readRootEnv('AUTH_SUPERUSER_PASSWORD', 'admin'),
  feedPath: path.join(rootDir, 'backend', 'element.xml'),
}

export default defineConfig({
  testDir: './e2e',
  // фид весит 16 МБ и грузится дважды — по разу на транспорт
  timeout: 5 * 60 * 1000,
  expect: { timeout: 15_000 },
  forbidOnly: !!process.env.CI,
  retries: 0,
  // сценарий меняет активный набор — параллельные воркеры мешали бы друг другу
  workers: 1,
  reporter: 'list',
  use: {
    actionTimeout: 30_000,
    baseURL: process.env.E2E_BASE_URL ?? 'http://localhost:5173',
    trace: 'retain-on-failure',
    headless: true,
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  /** Если стек уже поднят (`docker compose up` отдаёт фронт на 5173) — переиспользуем его;
   *  иначе поднимается vite dev, который проксирует /api на локальный бэкенд. */
  webServer: {
    command: 'pnpm dev',
    port: 5173,
    reuseExistingServer: true,
    timeout: 120_000,
  },
})
