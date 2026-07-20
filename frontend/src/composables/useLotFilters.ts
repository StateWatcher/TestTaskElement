/** Фильтры каталога живут в query-строке роутера, а не в локальном ref.
 *
 * Так ссылка с фильтрами шарится и переживает F5, а «источник правды» один:
 * экран просто следит за `query` и перезапрашивает страницу. */

import { computed } from 'vue'
import { useRoute, useRouter, type LocationQuery } from 'vue-router'

import { DEFAULT_LOT_QUERY, LOT_SORT_FIELDS, LOT_STATUSES, type LotQuery } from '@/domain'

export function useLotFilters() {
  const route = useRoute()
  const router = useRouter()

  const query = computed<LotQuery>(() => parse(route.query))

  /** Любая правка фильтра сбрасывает страницу — иначе после сужения выборки
   *  можно оказаться на несуществующей странице. */
  function update(patch: Partial<LotQuery>): void {
    const next: LotQuery = { ...query.value, ...patch }
    if (patch.page === undefined) next.page = 1
    void router.replace({ query: serialize(next) })
  }

  function reset(): void {
    void router.replace({ query: {} })
  }

  return { query, update, reset }
}

function parse(source: LocationQuery): LotQuery {
  return {
    project: single(source.project) || undefined,
    rooms: numbers(source.rooms),
    priceM2Min: number(single(source.priceMin)),
    priceM2Max: number(single(source.priceMax)),
    status: oneOf(single(source.status), LOT_STATUSES),
    sort: oneOf(single(source.sort), LOT_SORT_FIELDS) ?? DEFAULT_LOT_QUERY.sort,
    order: oneOf(single(source.order), ['asc', 'desc'] as const) ?? DEFAULT_LOT_QUERY.order,
    page: number(single(source.page)) ?? DEFAULT_LOT_QUERY.page,
    pageSize: number(single(source.pageSize)) ?? DEFAULT_LOT_QUERY.pageSize,
  }
}

function serialize(query: LotQuery): LocationQuery {
  const result: LocationQuery = {}
  if (query.project) result.project = query.project
  if (query.rooms?.length) result.rooms = query.rooms.join(',')
  if (query.priceM2Min !== undefined) result.priceMin = String(query.priceM2Min)
  if (query.priceM2Max !== undefined) result.priceMax = String(query.priceM2Max)
  if (query.status) result.status = query.status
  if (query.sort !== DEFAULT_LOT_QUERY.sort) result.sort = query.sort
  if (query.order !== DEFAULT_LOT_QUERY.order) result.order = query.order
  if (query.page !== DEFAULT_LOT_QUERY.page) result.page = String(query.page)
  if (query.pageSize !== DEFAULT_LOT_QUERY.pageSize) result.pageSize = String(query.pageSize)
  return result
}

type QueryValue = LocationQuery[string] | undefined

function single(value: QueryValue): string | undefined {
  const first = Array.isArray(value) ? value[0] : value
  return first ?? undefined
}

function number(value: string | undefined): number | undefined {
  if (value === undefined || value === '') return undefined
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : undefined
}

function numbers(value: QueryValue): number[] | undefined {
  const raw = single(value)
  if (!raw) return undefined
  const parsed = raw
    .split(',')
    .map((item) => Number(item))
    .filter((item) => Number.isInteger(item))
  return parsed.length ? parsed : undefined
}

function oneOf<T extends string>(value: string | undefined, allowed: readonly T[]): T | undefined {
  return allowed.includes(value as T) ? (value as T) : undefined
}
