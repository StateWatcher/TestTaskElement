/** Ошибка REST живёт в HTTP-статусе, а тело бывает двух форм:
 *  - доменная ошибка бэкенда: `{"detail": {"code", "message"}}` (401/404/409/422);
 *  - валидация FastAPI:       `{"detail": [{loc, msg, type}, …]}` (422).
 *  Поэтому статус даёт вид ошибки, а сообщение приходится вытаскивать разбором. */

import { ApiError, type ApiErrorKind } from '../types'

const KIND_BY_STATUS: Record<number, ApiErrorKind> = {
  400: 'validation',
  401: 'unauthorized',
  403: 'unauthorized',
  404: 'notFound',
  409: 'conflict',
  422: 'validation',
}

export function restError(status: number, body: unknown): ApiError {
  const kind: ApiErrorKind = KIND_BY_STATUS[status] ?? 'server'
  const detail = isRecord(body) ? body.detail : undefined

  if (isRecord(detail) && typeof detail.message === 'string') {
    return new ApiError(kind, detail.message, asString(detail.code), detail)
  }
  if (Array.isArray(detail)) {
    return new ApiError(kind, validationMessage(detail), 'validation_error', detail)
  }
  if (typeof detail === 'string') {
    return new ApiError(kind, detail, undefined, body)
  }
  return new ApiError(kind, `Ошибка запроса (HTTP ${status})`, undefined, body)
}

function validationMessage(errors: unknown[]): string {
  const messages = errors
    .map((error) => (isRecord(error) && typeof error.msg === 'string' ? error.msg : null))
    .filter((message): message is string => message !== null)
  return messages.length ? messages.join('; ') : 'Некорректные данные запроса'
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function asString(value: unknown): string | undefined {
  return typeof value === 'string' ? value : undefined
}
