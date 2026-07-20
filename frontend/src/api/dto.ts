/** Граница «провод → домен»: zod-схемы ответов и мапперы, общие для обоих транспортов.
 *
 * Общие они не по лени: REST-роутер и JSON-RPC-метод на бэкенде сериализуют одни и те же
 * Pydantic-схемы, поэтому payload у транспортов совпадает побайтово — различается только
 * конверт (URL и статус против envelope и кода ошибки). Две копии мапперов были бы
 * дублированием ради симметрии; транспортно-специфичны только клиент и разбор ошибок.
 *
 * Decimal бэкенд отдаёт строкой ("10000000.00"), даты — ISO-строкой: конвертация здесь.
 */

import { z } from 'zod'

import {
  APPLICATION_STATUSES,
  BOOKING_STATUSES,
  LOT_STATUSES,
  type Application,
  type Booking,
  type FeedUploadResult,
  type Lot,
  type LotQuery,
  type LotSet,
  type Page,
  type PageQuery,
  type Session,
} from '@/domain'

/** Decimal приезжает строкой; number принимаем на случай смены сериализации. */
const numeric = z.union([z.string(), z.number()]).transform(Number)
const timestamp = z.string().transform((value) => new Date(value))

const lotSchema = z.object({
  id: z.number(),
  external_id: z.string(),
  set_id: z.number(),
  project: z.string(),
  address: z.string(),
  rooms: z.number(),
  area: numeric,
  floor: z.number(),
  price: numeric,
  price_base: numeric,
  price_per_m2: numeric.nullable(),
  status: z.enum(LOT_STATUSES),
  created_at: timestamp,
  updated_at: timestamp,
})

const bookingSchema = z.object({
  id: z.number(),
  lot_id: z.number(),
  name: z.string(),
  contact: z.string(),
  status: z.enum(BOOKING_STATUSES),
  created_at: timestamp,
  lot: lotSchema.nullish(),
})

const applicationSchema = z.object({
  id: z.number(),
  lot_id: z.number().nullable(),
  name: z.string(),
  contact: z.string(),
  comment: z.string(),
  status: z.enum(APPLICATION_STATUSES),
  created_at: timestamp,
  lot: lotSchema.nullish(),
})

const lotSetSchema = z.object({
  id: z.number(),
  name: z.string(),
  uploaded_at: timestamp,
  lots_count: z.number(),
  is_active: z.boolean(),
})

const feedUploadResultSchema = z.object({ set: lotSetSchema, skipped: z.number() })
const sessionSchema = z.object({ login: z.string() })
const projectsSchema = z.array(z.string())

const pageSchema = <T extends z.ZodType>(item: T) =>
  z.object({ items: z.array(item), total: z.number(), page: z.number(), page_size: z.number() })

// --- мапперы: единственное место, где snake_case превращается в домен ---
//
// Парсинг и маппинг разделены: вложенный лот (в брони и заявке) схема разбирает
// вместе с родителем, и повторно скармливать его `parse` уже нельзя — там,
// например, вместо ISO-строки лежит Date.

function lotFromDto(dto: z.infer<typeof lotSchema>): Lot {
  return {
    id: dto.id,
    externalId: dto.external_id,
    setId: dto.set_id,
    project: dto.project,
    address: dto.address,
    rooms: dto.rooms,
    area: dto.area,
    floor: dto.floor,
    price: dto.price,
    priceBase: dto.price_base,
    pricePerM2: dto.price_per_m2,
    status: dto.status,
    createdAt: dto.created_at,
    updatedAt: dto.updated_at,
  }
}

export function toLot(raw: unknown): Lot {
  return lotFromDto(lotSchema.parse(raw))
}

export function toBooking(raw: unknown): Booking {
  const dto = bookingSchema.parse(raw)
  return {
    id: dto.id,
    lotId: dto.lot_id,
    name: dto.name,
    contact: dto.contact,
    status: dto.status,
    createdAt: dto.created_at,
    lot: dto.lot ? lotFromDto(dto.lot) : null,
  }
}

export function toApplication(raw: unknown): Application {
  const dto = applicationSchema.parse(raw)
  return {
    id: dto.id,
    lotId: dto.lot_id,
    name: dto.name,
    contact: dto.contact,
    comment: dto.comment,
    status: dto.status,
    createdAt: dto.created_at,
    lot: dto.lot ? lotFromDto(dto.lot) : null,
  }
}

function lotSetFromDto(dto: z.infer<typeof lotSetSchema>): LotSet {
  return {
    id: dto.id,
    name: dto.name,
    uploadedAt: dto.uploaded_at,
    lotsCount: dto.lots_count,
    isActive: dto.is_active,
  }
}

export function toLotSet(raw: unknown): LotSet {
  return lotSetFromDto(lotSetSchema.parse(raw))
}

export function toFeedUploadResult(raw: unknown): FeedUploadResult {
  const dto = feedUploadResultSchema.parse(raw)
  return { set: lotSetFromDto(dto.set), skipped: dto.skipped }
}

export function toSession(raw: unknown): Session {
  return sessionSchema.parse(raw)
}

export function toProjects(raw: unknown): string[] {
  return projectsSchema.parse(raw)
}

/** Страница любого элемента: схема проверяет конверт, маппер — элементы. */
export function toPage<T>(raw: unknown, item: (value: unknown) => T): Page<T> {
  const dto = pageSchema(z.unknown()).parse(raw)
  return {
    items: dto.items.map(item),
    total: dto.total,
    page: dto.page,
    pageSize: dto.page_size,
  }
}

// --- сериализация запросов: тоже общая, различается только упаковка ---

/** Плоский набор параметров бэкенда. REST раскладывает его в query-string
 *  (`rooms` — повторяющийся ключ), JSON-RPC кладёт как объект `params`. */
export type WireParams = Record<string, string | number | boolean | number[]>

export function lotQueryToParams(query: LotQuery): WireParams {
  const params: WireParams = {
    sort: query.sort,
    order: query.order,
    page: query.page,
    page_size: query.pageSize,
  }
  if (query.project) params.project = query.project
  if (query.rooms?.length) params.rooms = query.rooms
  if (query.priceM2Min !== undefined) params.price_m2_min = query.priceM2Min
  if (query.priceM2Max !== undefined) params.price_m2_max = query.priceM2Max
  if (query.status) params.status = query.status
  return params
}

export function pageQueryToParams(query: PageQuery & { status?: string }): WireParams {
  const params: WireParams = { page: query.page, page_size: query.pageSize }
  if (query.status) params.status = query.status
  return params
}

export function toSearchParams(params: WireParams): URLSearchParams {
  const search = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (Array.isArray(value)) {
      for (const item of value) search.append(key, String(item))
    } else {
      search.append(key, String(value))
    }
  }
  return search
}
