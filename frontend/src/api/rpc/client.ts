/** JSON-RPC-реализация ApiClient: один эндпоинт, имя метода, типизированные params.
 *
 * Действия-глаголы (`admin.sets.activate`) выражаются естественно, зато у протокола
 * нет multipart — файл приходится слать base64, и нет статусов — ошибка приезжает
 * в теле HTTP 200.
 */

import type { ApiClient } from '../types'
import { ApiError } from '../types'
import { http, UPLOAD_TIMEOUT_MS } from '../http'
import {
  lotQueryToParams,
  pageQueryToParams,
  toApplication,
  toBooking,
  toFeedUploadResult,
  toLot,
  toLotSet,
  toPage,
  toProjects,
  toSession,
  type WireParams,
} from '../dto'
import { rpcError, type RpcErrorPayload } from './errors'

const ENDPOINT = '/jsonrpc'

let requestId = 0

async function call(method: string, params?: WireParams, timeoutMs?: number): Promise<unknown> {
  const { status, body } = await http(ENDPOINT, {
    method: 'POST',
    json: { jsonrpc: '2.0', id: ++requestId, method, params: params ?? {} },
    timeoutMs,
  })

  // сам эндпоинт обязан отвечать 200: не-200 — это сбой транспорта, а не домена
  if (status !== 200 || typeof body !== 'object' || body === null) {
    throw new ApiError('server', `Некорректный ответ JSON-RPC (HTTP ${status})`, undefined, body)
  }

  const envelope = body as { result?: unknown; error?: RpcErrorPayload }
  if (envelope.error) throw rpcError(envelope.error)
  return envelope.result
}

/** У протокола нет multipart: 16-МБ фид уезжает base64. readAsDataURL кодирует
 *  файл целиком силами браузера — ручной btoa по чанкам на таком размере только
 *  тратит время и рискует переполнить стек. */
function toBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onerror = () => reject(new ApiError('validation', 'Не удалось прочитать файл'))
    reader.onload = () => {
      const result = String(reader.result)
      resolve(result.slice(result.indexOf(',') + 1))
    }
    reader.readAsDataURL(file)
  })
}

export function createRpcClient(): ApiClient {
  return {
    lots: {
      async list(query) {
        return toPage(await call('lots.list', lotQueryToParams(query)), toLot)
      },
      async get(id) {
        return toLot(await call('lots.get', { lot_id: id }))
      },
      async projects() {
        return toProjects(await call('lots.projects'))
      },
    },

    bookings: {
      async create(input) {
        const params = { lot_id: input.lotId, name: input.name, contact: input.contact }
        return toBooking(await call('bookings.create', params))
      },
      async list(query) {
        return toPage(await call('admin.bookings.list', pageQueryToParams(query)), toBooking)
      },
      async cancel(id) {
        return toBooking(await call('admin.bookings.cancel', { booking_id: id }))
      },
    },

    applications: {
      async create(input) {
        const params: WireParams = {
          name: input.name,
          contact: input.contact,
          comment: input.comment,
        }
        if (input.lotId !== undefined) params.lot_id = input.lotId
        return toApplication(await call('requests.create', params))
      },
      async list(query) {
        return toPage(await call('admin.requests.list', pageQueryToParams(query)), toApplication)
      },
      async setStatus(id, status) {
        return toApplication(await call('admin.requests.set_status', { request_id: id, status }))
      },
    },

    sets: {
      async upload(file) {
        const params = { filename: file.name, content_base64: await toBase64(file) }
        return toFeedUploadResult(await call('admin.sets.upload', params, UPLOAD_TIMEOUT_MS))
      },
      async list(query) {
        return toPage(await call('admin.sets.list', pageQueryToParams(query)), toLotSet)
      },
      async activate(id) {
        return toLotSet(await call('admin.sets.activate', { set_id: id }))
      },
    },

    auth: {
      async login(login, password) {
        return toSession(await call('auth.login', { login, password }))
      },
      async logout() {
        await call('auth.logout')
      },
      async me() {
        return toSession(await call('auth.me'))
      },
    },
  }
}
