/** Ядро абстракции транспорта: две разные сигнализации об ошибке дают
 *  одну доменную таксономию. Опорный кейс — бронь занятого лота: HTTP 409
 *  в REST и код -32003 в JSON-RPC приходят в UI как один `conflict`. */

import { describe, expect, it } from 'vitest'

import { restError } from '../rest/errors'
import { RPC_CODES, rpcError } from '../rpc/errors'
import type { ApiErrorKind } from '../types'

describe('нормализация ошибок транспортов', () => {
  const cases: { kind: ApiErrorKind; status: number; code: number }[] = [
    { kind: 'unauthorized', status: 401, code: RPC_CODES.UNAUTHORIZED },
    { kind: 'notFound', status: 404, code: RPC_CODES.NOT_FOUND },
    { kind: 'conflict', status: 409, code: RPC_CODES.CONFLICT },
    { kind: 'validation', status: 422, code: RPC_CODES.UNPROCESSABLE },
    { kind: 'server', status: 500, code: RPC_CODES.INTERNAL_ERROR },
  ]

  it.each(cases)('$status в REST и $code в RPC дают $kind', ({ kind, status, code }) => {
    const rest = restError(status, { detail: { code: 'x', message: 'сообщение' } })
    const rpc = rpcError({ code, message: 'сообщение', data: { code: 'x' } })

    expect(rest.kind).toBe(kind)
    expect(rpc.kind).toBe(kind)
  })

  it('бронь занятого лота одинаково доезжает из обоих транспортов', () => {
    const message = 'Лот недоступен для брони'
    const rest = restError(409, { detail: { code: 'lot_not_available', message } })
    const rpc = rpcError({
      code: RPC_CODES.CONFLICT,
      message,
      data: { code: 'lot_not_available' },
    })

    for (const error of [rest, rpc]) {
      expect(error.kind).toBe('conflict')
      expect(error.code).toBe('lot_not_available')
      expect(error.message).toBe(message)
    }
  })

  it('валидация FastAPI приезжает массивом, а не объектом', () => {
    const error = restError(422, {
      detail: [
        { loc: ['body', 'contact'], msg: 'String should have at least 3 characters' },
        { loc: ['body', 'name'], msg: 'Field required' },
      ],
    })

    expect(error.kind).toBe('validation')
    expect(error.message).toContain('at least 3 characters')
    expect(error.message).toContain('Field required')
  })

  it('протокольные коды JSON-RPC — это серверная ошибка для UI', () => {
    expect(rpcError({ code: RPC_CODES.METHOD_NOT_FOUND, message: 'x' }).kind).toBe('server')
    expect(rpcError({ code: RPC_CODES.PARSE_ERROR, message: 'x' }).kind).toBe('server')
    expect(rpcError({ code: RPC_CODES.INVALID_PARAMS, message: 'x' }).kind).toBe('validation')
  })

  it('тело без detail не роняет разбор', () => {
    const error = restError(503, 'Service Unavailable')
    expect(error.kind).toBe('server')
    expect(error.message).toContain('503')
  })
})
