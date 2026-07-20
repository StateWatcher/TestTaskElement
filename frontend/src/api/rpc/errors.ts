/** У JSON-RPC своя семантика ошибок поверх HTTP 200: вид берётся из кода в теле.
 *  Коды -32001..-32004 — доменные (см. `_DOMAIN_CODES` в диспетчере бэкенда),
 *  остальные -32xxx — протокольные, для UI это «серверная ошибка».
 *  Доменный код (`lot_not_available`, …) бэкенд кладёт в `error.data.code`. */

import { ApiError, type ApiErrorKind } from '../types'

export const RPC_CODES = {
  PARSE_ERROR: -32700,
  INVALID_REQUEST: -32600,
  METHOD_NOT_FOUND: -32601,
  INVALID_PARAMS: -32602,
  INTERNAL_ERROR: -32603,
  SERVER_ERROR: -32000,
  UNAUTHORIZED: -32001,
  NOT_FOUND: -32002,
  CONFLICT: -32003,
  UNPROCESSABLE: -32004,
} as const

const KIND_BY_CODE: Record<number, ApiErrorKind> = {
  [RPC_CODES.UNAUTHORIZED]: 'unauthorized',
  [RPC_CODES.NOT_FOUND]: 'notFound',
  [RPC_CODES.CONFLICT]: 'conflict',
  [RPC_CODES.UNPROCESSABLE]: 'validation',
  [RPC_CODES.INVALID_PARAMS]: 'validation',
}

export interface RpcErrorPayload {
  code: number
  message: string
  data?: unknown
}

export function rpcError(error: RpcErrorPayload): ApiError {
  const kind: ApiErrorKind = KIND_BY_CODE[error.code] ?? 'server'
  return new ApiError(kind, error.message, domainCode(error.data), error.data)
}

function domainCode(data: unknown): string | undefined {
  if (typeof data === 'object' && data !== null && 'code' in data) {
    const code = (data as { code: unknown }).code
    if (typeof code === 'string') return code
  }
  return undefined
}
