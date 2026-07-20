import { defineStore } from 'pinia'

import { api } from '@/api'
import {
  emptyPage,
  type Application,
  type ApplicationInput,
  type ApplicationQuery,
  type ApplicationStatus,
  type Page,
} from '@/domain'
import { notifyApiError } from '@/lib/notify'
import { useAsyncResource } from '@/stores/asyncResource'

export const useApplicationsStore = defineStore('applications', () => {
  const pageResource = useAsyncResource<Page<Application>>(emptyPage<Application>())

  function fetchPage(query: ApplicationQuery): Promise<void> {
    return pageResource.run(
      () => api().applications.list(query),
      () => emptyPage<Application>(query.page, query.pageSize),
    )
  }

  async function create(input: ApplicationInput): Promise<Application> {
    return api().applications.create(input)
  }

  async function setStatus(id: number, status: ApplicationStatus): Promise<boolean> {
    try {
      const updated = await api().applications.setStatus(id, status)
      const index = pageResource.data.value.items.findIndex(
        (application) => application.id === id,
      )
      if (index !== -1) pageResource.data.value.items[index] = updated
      return true
    } catch (error) {
      notifyApiError(error)
      return false
    }
  }

  return { page: pageResource.data, loading: pageResource.loading, fetchPage, create, setStatus }
})
