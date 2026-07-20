/** Сквозной смоук, прогоняемый через оба транспорта одним и тем же сценарием.
 *
 * Смысл именно в повторении: переключатель в шапке меняет только конверт запросов,
 * поэтому идентичный набор шагов обязан давать идентичный результат. По сигналу
 * качества один такой прогон ценнее набора юнитов на сторы.
 *
 * Требует поднятого стека: `docker compose up` (или бэкенд на :8000 + `pnpm dev`).
 */

import { expect, test, type Page } from '@playwright/test'

import { E2E } from '../playwright.config'

const TRANSPORTS = [
  { id: 'rest', label: 'REST' },
  { id: 'rpc', label: 'JSON-RPC' },
] as const

/** Тост, а не любой текст на странице: `getByText` ищет подстроку без учёта регистра
 *  и цепляет, например, кнопку «Бронь недоступна: лот забронирован». */
function toast(page: Page, text: string | RegExp) {
  return page.locator('[data-sonner-toast]').filter({ hasText: text })
}

async function selectTransport(page: Page, label: string): Promise<void> {
  await page.getByTestId('transport-switch').click()
  await page.getByRole('option', { name: label, exact: true }).click()
  await expect(page.getByTestId('transport-switch')).toContainText(label)
}

async function login(page: Page): Promise<void> {
  await page.goto('/admin/login')
  await page.locator('#login').fill(E2E.login)
  await page.locator('#password').fill(E2E.password)
  await page.getByTestId('login-submit').click()
  await expect(page).toHaveURL(/\/admin\/sets/)
}

async function uploadAndActivateFeed(page: Page): Promise<void> {
  await page.goto('/admin/sets')
  await page.getByTestId('feed-input').setInputFiles(E2E.feedPath)
  await page.getByTestId('feed-upload').click()

  // разбор 16-МБ фида занимает десятки секунд
  await expect(toast(page, /Загружено лотов/)).toBeVisible({ timeout: 240_000 })

  // наборы immutable: свежий набор — первая строка, её и активируем
  const activateButtons = page.getByTestId('activate-set')
  if (await activateButtons.first().isVisible()) {
    await activateButtons.first().click()
  }
  await expect(page.getByTestId('set-row').first().getByText('Активный')).toBeVisible()
}

/** Возвращает id первого лота «в продаже». */
async function openLotInSale(page: Page): Promise<number> {
  await page.goto('/lots?status=in_sale')
  await expect(page.getByTestId('lot-row').first()).toBeVisible()
  await page.getByTestId('lot-row').first().getByRole('link', { name: 'Открыть' }).click()

  await expect(page.getByTestId('book-lot')).toBeVisible()
  const id = Number(new URL(page.url()).pathname.split('/').pop())
  expect(Number.isInteger(id)).toBe(true)
  return id
}

for (const transport of TRANSPORTS) {
  test.describe(`транспорт ${transport.label}`, () => {
    test('фид → активация → бронь → конфликт повторной брони', async ({ page }) => {
      await page.goto('/')
      await selectTransport(page, transport.label)

      await login(page)
      await uploadAndActivateFeed(page)

      // --- бронь проходит ---
      await openLotInSale(page)
      await page.getByTestId('book-lot').click()
      await page.locator('#booking-name').fill('Тест Тестович')
      await page.locator('#booking-contact').fill('+7 900 000-00-00')
      await page.getByTestId('booking-submit').click()

      await expect(toast(page, 'Лот забронирован')).toBeVisible()
      await expect(page.getByTestId('book-lot-disabled')).toBeVisible()

      // --- повторная бронь того же лота даёт конфликт ---
      // Лот занимаем в обход UI (кнопка на забронированном лоте уже заблокирована),
      // а сам конфликт ловим штатной формой: бэкенд ответит 409 в REST и -32003 в RPC,
      // и то и другое обязано превратиться в один и тот же тост.
      const lotId = await openLotInSale(page)
      await page.getByTestId('book-lot').click()

      const response = await page.request.post('/api/bookings', {
        data: { lot_id: lotId, name: 'Гонщик', contact: 'race@example.com' },
      })
      expect(response.status()).toBe(201)

      await page.locator('#booking-name').fill('Тест Тестович')
      await page.locator('#booking-contact').fill('+7 900 000-00-01')
      await page.getByTestId('booking-submit').click()

      const conflict = toast(page, 'Действие невозможно')
      await expect(conflict).toBeVisible()
      await expect(conflict).toContainText('Лот недоступен для брони')
    })

    test('заявка доезжает до админки', async ({ page }) => {
      await page.goto('/')
      await selectTransport(page, transport.label)

      const comment = `Смоук ${transport.id} ${Date.now()}`

      await page.goto('/lots')
      await expect(page.getByTestId('lot-row').first()).toBeVisible()
      await page.getByTestId('lot-row').first().getByRole('link', { name: 'Открыть' }).click()

      await page.getByTestId('create-application').click()
      await page.locator('#application-name').fill('Заявитель')
      await page.locator('#application-contact').fill('mail@example.com')
      await page.locator('#application-comment').fill(comment)
      await page.getByTestId('application-submit').click()
      await expect(toast(page, 'Заявка отправлена')).toBeVisible()

      await login(page)
      await page.goto('/admin/requests')
      await expect(page.getByText(comment)).toBeVisible()
    })
  })
}
