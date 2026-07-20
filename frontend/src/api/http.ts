/** Тонкая обёртка над fetch: базовый URL, cookie-сессия, таймаут.
 *
 * Решение «ошибка это или нет» принимает транспорт, а не эта функция: REST смотрит
 * на статус, JSON-RPC — в тело 200-ответа. Поэтому наружу отдаётся сырая пара
 * (status, body), а брошенная ошибка здесь означает только сетевой сбой.
 */

import { ApiError } from './types'

/** По умолчанию относительный путь: в dev его проксирует Vite, в docker — nginx.
 *  Переменная нужна лишь для сборки, обращающейся к бэкенду напрямую. */
const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '/api'

/** Обычный запрос столько не длится: таймаут страхует только подвисшее соединение. */
export const DEFAULT_TIMEOUT_MS = 15_000
/** Разбор 16-МБ фида на бэкенде занимает десятки секунд — отсюда запас. */
export const UPLOAD_TIMEOUT_MS = 180_000

export interface HttpResponse {
  status: number
  body: unknown
}

export interface HttpOptions {
  method?: string
  /** JSON-тело; для multipart передавайте FormData через `formData` */
  json?: unknown
  formData?: FormData
  query?: URLSearchParams
  timeoutMs?: number
}

export async function http(path: string, options: HttpOptions = {}): Promise<HttpResponse> {
  const { method = 'GET', json, formData, query, timeoutMs = DEFAULT_TIMEOUT_MS } = options
  const url = `${BASE_URL}${path}${query?.size ? `?${query}` : ''}`

  const init: RequestInit = {
    method,
    // сессия админа — HttpOnly-cookie, JS её не видит и не отправляет без этого
    credentials: 'include',
    signal: AbortSignal.timeout(timeoutMs),
  }
  if (formData) {
    init.body = formData // Content-Type с boundary проставит браузер
  } else if (json !== undefined) {
    init.body = JSON.stringify(json)
    init.headers = { 'Content-Type': 'application/json' }
  }

  let response: Response
  try {
    response = await fetch(url, init)
  } catch (error) {
    throw toNetworkError(error)
  }

  return { status: response.status, body: await readBody(response) }
}

async function readBody(response: Response): Promise<unknown> {
  if (response.status === 204) return undefined
  const text = await response.text()
  if (!text) return undefined
  try {
    return JSON.parse(text)
  } catch {
    return text
  }
}

function toNetworkError(error: unknown): ApiError {
  const timedOut = error instanceof DOMException && error.name === 'TimeoutError'
  return new ApiError(
    'network',
    timedOut ? 'Сервер не ответил вовремя' : 'Не удалось связаться с сервером',
    timedOut ? 'timeout' : 'network_error',
    error,
  )
}
