/** Лот — квартира активного набора. Плоская модель: ЖК и адрес корпуса — просто поля. */

export const LOT_STATUSES = ['in_sale', 'booked', 'sold'] as const
export type LotStatus = (typeof LOT_STATUSES)[number]

export const LOT_STATUS_LABELS: Record<LotStatus, string> = {
  in_sale: 'В продаже',
  booked: 'Забронирован',
  sold: 'Продан',
}

export interface Lot {
  id: number
  externalId: string
  setId: number
  project: string
  address: string
  /** 0 — студия */
  rooms: number
  area: number
  floor: number
  price: number
  priceBase: number
  /** Считается бэкендом, не хранится; null, если площадь нулевая */
  pricePerM2: number | null
  status: LotStatus
  createdAt: Date
  updatedAt: Date
}

export const LOT_SORT_FIELDS = ['price', 'price_per_m2', 'area', 'floor', 'rooms'] as const
export type LotSortField = (typeof LOT_SORT_FIELDS)[number]

export type SortOrder = 'asc' | 'desc'

export interface LotQuery {
  project?: string
  rooms?: number[]
  priceM2Min?: number
  priceM2Max?: number
  status?: LotStatus
  sort: LotSortField
  order: SortOrder
  page: number
  pageSize: number
}

export const DEFAULT_LOT_QUERY: LotQuery = {
  sort: 'price',
  order: 'asc',
  page: 1,
  pageSize: 20,
}
