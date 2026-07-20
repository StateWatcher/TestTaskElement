/** Брони: публичное создание и админский список с отменой.
 *
 * `create` намеренно пробрасывает ошибку наружу: форме нужно знать про конфликт,
 * чтобы не закрывать диалог и перезагрузить лот. Списки же ошибку гасят тостом. */

import { defineStore } from 'pinia'

import { api } from '@/api'
import { emptyPage, type Booking, type BookingInput, type BookingQuery, type Page } from '@/domain'
import { notifyApiError } from '@/lib/notify'
import { useAsyncResource } from '@/stores/asyncResource'

export const useBookingsStore = defineStore('bookings', () => {
  const pageResource = useAsyncResource<Page<Booking>>(emptyPage<Booking>())

  function fetchPage(query: BookingQuery): Promise<void> {
    return pageResource.run(
      () => api().bookings.list(query),
      () => emptyPage<Booking>(query.page, query.pageSize),
    )
  }

  async function create(input: BookingInput): Promise<Booking> {
    return api().bookings.create(input)
  }

  async function cancel(id: number): Promise<boolean> {
    try {
      const cancelled = await api().bookings.cancel(id)
      const index = pageResource.data.value.items.findIndex((booking) => booking.id === id)
      if (index !== -1) pageResource.data.value.items[index] = cancelled
      return true
    } catch (error) {
      notifyApiError(error)
      return false
    }
  }

  return { page: pageResource.data, loading: pageResource.loading, fetchPage, create, cancel }
})
