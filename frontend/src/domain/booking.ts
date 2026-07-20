import type { Lot } from './lot'

export const BOOKING_STATUSES = ['active', 'cancelled'] as const
export type BookingStatus = (typeof BOOKING_STATUSES)[number]

export const BOOKING_STATUS_LABELS: Record<BookingStatus, string> = {
  active: 'Активна',
  cancelled: 'Отменена',
}

export interface Booking {
  id: number
  lotId: number
  name: string
  contact: string
  status: BookingStatus
  createdAt: Date
  lot: Lot | null
}

export interface BookingInput {
  lotId: number
  name: string
  contact: string
}

export interface BookingQuery {
  status?: BookingStatus
  page: number
  pageSize: number
}
