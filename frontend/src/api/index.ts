/** Резолвер транспорта — единственное место, где выбирается реализация.
 *
 * Сторы зовут `api()` в начале каждого экшена и никогда не держат ссылку на клиент:
 * иначе переключатель транспорта не подействовал бы на уже созданный стор.
 *
 * Осознанный минус: `api()` — скрытая зависимость от инициализированной Pinia
 * (в юнит-тестах нужен `createTestingPinia`). `provide/inject` чище концептуально,
 * но setup-сторы Pinia не умеют `inject`, а вызовы API рождаются именно в сторах.
 */

import { useTransportStore } from '@/stores/transport'

import { createRestClient } from './rest/client'
import { createRpcClient } from './rpc/client'
import type { ApiClient, Transport } from './types'

const clients: Record<Transport, ApiClient> = {
  rest: createRestClient(),
  rpc: createRpcClient(),
}

export function api(): ApiClient {
  return clients[useTransportStore().transport]
}

export { ApiError } from './types'
export type { ApiClient, ApiErrorKind, Transport } from './types'
