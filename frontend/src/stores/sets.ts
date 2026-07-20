/** Наборы лотов: загрузка фида и выбор активного.
 *
 * Наборы immutable — повторная загрузка создаёт новый набор, а не обновляет старый,
 * поэтому список только растёт и пагинируется на сервере.
 *
 * Перезапрос после upload/activate инициирует вью, а не стор: запрос страницы живёт
 * во вью (как в брони и заявках), а патчем на месте здесь не обойтись — activate
 * меняет ещё и прежний активный набор, которого в ответе нет и который может лежать
 * на другой странице. */

import { defineStore } from 'pinia'
import { ref } from 'vue'

import { api } from '@/api'
import { emptyPage, type FeedUploadResult, type LotSet, type Page, type PageQuery } from '@/domain'
import { notifyApiError } from '@/lib/notify'
import { useAsyncResource } from '@/stores/asyncResource'

export const useSetsStore = defineStore('sets', () => {
  const pageResource = useAsyncResource<Page<LotSet>>(emptyPage<LotSet>())
  const uploading = ref(false)

  function fetchPage(query: PageQuery): Promise<void> {
    return pageResource.run(
      () => api().sets.list(query),
      () => emptyPage<LotSet>(query.page, query.pageSize),
    )
  }

  async function upload(file: File): Promise<FeedUploadResult | null> {
    uploading.value = true
    try {
      return await api().sets.upload(file)
    } catch (error) {
      notifyApiError(error)
      return null
    } finally {
      uploading.value = false
    }
  }

  async function activate(id: number): Promise<boolean> {
    try {
      await api().sets.activate(id)
      return true
    } catch (error) {
      notifyApiError(error)
      return false
    }
  }

  return {
    page: pageResource.data,
    loading: pageResource.loading,
    uploading,
    fetchPage,
    upload,
    activate,
  }
})
