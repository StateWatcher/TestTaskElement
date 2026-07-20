/** REST-реализация ApiClient: ресурс в URL, действие в HTTP-методе, ошибка в статусе.
 *
 * Действия, не ложащиеся на CRUD, оформлены POST-подресурсами
 * (`/bookings/{id}/cancel`, `/sets/{id}/activate`) — цена ресурсной модели.
 */

import type { ApiClient } from '../types'
import { http, UPLOAD_TIMEOUT_MS, type HttpOptions } from '../http'
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
  toSearchParams,
  toSession,
} from '../dto'
import { restError } from './errors'

async function call(path: string, options: HttpOptions = {}): Promise<unknown> {
  const { status, body } = await http(path, options)
  if (status >= 400) throw restError(status, body)
  return body
}

export function createRestClient(): ApiClient {
  return {
    lots: {
      async list(query) {
        const params = toSearchParams(lotQueryToParams(query))
        return toPage(await call('/lots', { query: params }), toLot)
      },
      async get(id) {
        return toLot(await call(`/lots/${id}`))
      },
      async projects() {
        return toProjects(await call('/lots/projects'))
      },
    },

    bookings: {
      async create(input) {
        const json = { lot_id: input.lotId, name: input.name, contact: input.contact }
        return toBooking(await call('/bookings', { method: 'POST', json }))
      },
      async list(query) {
        const params = toSearchParams(pageQueryToParams(query))
        return toPage(await call('/bookings', { query: params }), toBooking)
      },
      async cancel(id) {
        return toBooking(await call(`/bookings/${id}/cancel`, { method: 'POST' }))
      },
    },

    applications: {
      async create(input) {
        const json = {
          lot_id: input.lotId ?? null,
          name: input.name,
          contact: input.contact,
          comment: input.comment,
        }
        return toApplication(await call('/requests', { method: 'POST', json }))
      },
      async list(query) {
        const params = toSearchParams(pageQueryToParams(query))
        return toPage(await call('/requests', { query: params }), toApplication)
      },
      async setStatus(id, status) {
        return toApplication(await call(`/requests/${id}`, { method: 'PATCH', json: { status } }))
      },
    },

    sets: {
      async upload(file) {
        const formData = new FormData()
        formData.append('file', file)
        const body = await call('/sets', {
          method: 'POST',
          formData,
          timeoutMs: UPLOAD_TIMEOUT_MS,
        })
        return toFeedUploadResult(body)
      },
      async list(query) {
        const params = toSearchParams(pageQueryToParams(query))
        return toPage(await call('/sets', { query: params }), toLotSet)
      },
      async activate(id) {
        return toLotSet(await call(`/sets/${id}/activate`, { method: 'POST' }))
      },
    },

    auth: {
      async login(login, password) {
        return toSession(await call('/auth/login', { method: 'POST', json: { login, password } }))
      },
      async logout() {
        await call('/auth/logout', { method: 'POST' })
      },
      async me() {
        return toSession(await call('/auth/me'))
      },
    },
  }
}
