/** Мапперы — единственное место, где провод превращается в домен.
 *  Тест закрепляет два неочевидных факта контракта: Decimal приезжает строкой,
 *  а даты — ISO-строкой; и то и другое домен обязан видеть уже числом и Date. */

import { describe, expect, it } from 'vitest'

import {
  lotQueryToParams,
  toBooking,
  toFeedUploadResult,
  toLot,
  toLotSet,
  toPage,
  toSearchParams,
} from '../dto'
import { DEFAULT_LOT_QUERY } from '@/domain'

const lotDto = {
  id: 1,
  external_id: 'A-101',
  set_id: 7,
  project: 'BEREG.КУРОРТНЫЙ',
  address: 'корпус 1',
  rooms: 0,
  area: '50.50',
  floor: 3,
  price: '10000000.00',
  price_base: '9000000',
  price_per_m2: '198019.80',
  status: 'in_sale',
  created_at: '2026-07-19T21:43:26.521674Z',
  updated_at: '2026-07-19T21:43:26.521800Z',
}

describe('мапперы DTO → домен', () => {
  it('строки Decimal становятся числами, ISO-даты — Date', () => {
    const lot = toLot(lotDto)

    expect(lot.price).toBe(10_000_000)
    expect(lot.area).toBe(50.5)
    expect(lot.pricePerM2).toBe(198_019.8)
    expect(lot.externalId).toBe('A-101')
    expect(lot.createdAt).toBeInstanceOf(Date)
    expect(lot.createdAt.getUTCFullYear()).toBe(2026)
  })

  it('нулевая площадь даёт price_per_m2 = null, а не NaN', () => {
    const lot = toLot({ ...lotDto, area: '0', price_per_m2: null })

    expect(lot.pricePerM2).toBeNull()
  })

  it('вложенный лот брони разбирается тем же маппером', () => {
    const booking = toBooking({
      id: 5,
      lot_id: 1,
      name: 'Иван',
      contact: '+7 900 000-00-00',
      status: 'active',
      created_at: '2026-07-19T21:43:26Z',
      lot: lotDto,
    })

    expect(booking.lot?.price).toBe(10_000_000)
    expect(booking.lotId).toBe(1)
  })

  it('бронь без вложенного лота не падает', () => {
    const booking = toBooking({
      id: 5,
      lot_id: 1,
      name: 'Иван',
      contact: 'mail@example.com',
      status: 'cancelled',
      created_at: '2026-07-19T21:43:26Z',
      lot: null,
    })

    expect(booking.lot).toBeNull()
  })

  it('конверт страницы переводится в camelCase', () => {
    const page = toPage({ items: [lotDto], total: 3685, page: 2, page_size: 20 }, toLot)

    expect(page.pageSize).toBe(20)
    expect(page.total).toBe(3685)
    expect(page.items).toHaveLength(1)
  })

  it('вложенный набор в результате загрузки не разбирается дважды', () => {
    // регрессия: схема уже превратила uploaded_at в Date, повторный parse на нём падал
    const result = toFeedUploadResult({
      set: {
        id: 2,
        name: 'element.xml',
        uploaded_at: '2026-07-20T17:04:56.900Z',
        lots_count: 3685,
        is_active: false,
      },
      skipped: 0,
    })

    expect(result.set.lotsCount).toBe(3685)
    expect(result.set.uploadedAt).toBeInstanceOf(Date)
    expect(result.skipped).toBe(0)
  })

  it('страница наборов разбирается поэлементно', () => {
    const sets = toPage(
      {
        items: [
          {
            id: 1,
            name: 'element.xml',
            uploaded_at: '2026-07-19T20:46:00Z',
            lots_count: 3685,
            is_active: true,
          },
        ],
        total: 1,
        page: 1,
        page_size: 20,
      },
      toLotSet,
    )

    expect(sets.items).toHaveLength(1)
    expect(sets.items[0]?.isActive).toBe(true)
    expect(sets.items[0]?.uploadedAt).toBeInstanceOf(Date)
  })

  it('битый ответ отвергается схемой, а не течёт в UI', () => {
    expect(() => toLot({ ...lotDto, status: 'unknown_status' })).toThrow(/Invalid option/)
    expect(() => toLot({ ...lotDto, id: 'первый' })).toThrow(/expected number/)
  })
})

describe('сериализация запроса — общая для обоих транспортов', () => {
  it('пустые фильтры не уезжают на бэкенд', () => {
    const params = lotQueryToParams(DEFAULT_LOT_QUERY)

    expect(params).toEqual({ sort: 'price', order: 'asc', page: 1, page_size: 20 })
    expect('rooms' in params).toBe(false)
  })

  it('комнатность уходит массивом в RPC и повторяющимся ключом в REST', () => {
    const params = lotQueryToParams({ ...DEFAULT_LOT_QUERY, rooms: [0, 2], priceM2Min: 100 })

    expect(params.rooms).toEqual([0, 2])
    expect(params.price_m2_min).toBe(100)
    expect(toSearchParams(params).getAll('rooms')).toEqual(['0', '2'])
  })

  it('пустой список комнатности эквивалентен отсутствию фильтра', () => {
    expect('rooms' in lotQueryToParams({ ...DEFAULT_LOT_QUERY, rooms: [] })).toBe(false)
  })
})
