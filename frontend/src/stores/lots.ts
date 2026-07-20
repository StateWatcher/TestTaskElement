/** Каталог: страница лотов активного набора, список ЖК для фильтра и текущий лот.
 *
 * Fetch/loading/защита от гонки — в `useAsyncResource` (см. её комментарий); здесь только
 * то, что специфично лотам: три независимых ресурса с собственными счётчиками поколений,
 * чтобы, например, смена фильтра не мешала параллельно летящему `fetchLot`. */

import { defineStore } from 'pinia'

import { api } from '@/api'
import { emptyPage, type Lot, type LotQuery, type Page } from '@/domain'
import { useAsyncResource } from '@/stores/asyncResource'

export const useLotsStore = defineStore('lots', () => {
  const pageResource = useAsyncResource<Page<Lot>>(emptyPage<Lot>())
  const projectsResource = useAsyncResource<string[]>([], false)
  const lotResource = useAsyncResource<Lot | null>(null)

  function fetchPage(query: LotQuery): Promise<void> {
    return pageResource.run(
      () => api().lots.list(query),
      () => emptyPage<Lot>(query.page, query.pageSize),
    )
  }

  function fetchProjects(): Promise<void> {
    return projectsResource.run(
      () => api().lots.projects(),
      () => [],
    )
  }

  function fetchLot(id: number): Promise<void> {
    return lotResource.run(
      () => api().lots.get(id),
      () => null,
    )
  }

  return {
    page: pageResource.data,
    projects: projectsResource.data,
    current: lotResource.data,
    loading: pageResource.loading,
    lotLoading: lotResource.loading,
    fetchPage,
    fetchProjects,
    fetchLot,
  }
})
