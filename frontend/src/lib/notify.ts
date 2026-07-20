/** Единственное место, где ApiError превращается в UI.
 *
 * Вид ошибки уже нормализован клиентом транспорта, поэтому тексту всё равно,
 * пришёл ли конфликт как HTTP 409 или как код -32003.
 *
 * Здесь же централизован выход по 401: сессия могла истечь на любом запросе
 * любого транспорта, и держать эту обработку в каждом сторе — дублирование. */

import { toast } from 'vue-sonner'

import { ApiError, type ApiErrorKind } from '@/api'
import router from '@/router'
import { useAuthStore } from '@/stores/auth'

const TITLES: Record<ApiErrorKind, string> = {
  validation: 'Проверьте данные',
  notFound: 'Не найдено',
  conflict: 'Действие невозможно',
  unauthorized: 'Нужна авторизация',
  server: 'Ошибка сервера',
  network: 'Нет связи с сервером',
}

export function notifyApiError(error: unknown): ApiError {
  const apiError = toApiError(error)
  toast.error(TITLES[apiError.kind], { description: apiError.message })

  if (apiError.kind === 'unauthorized') {
    useAuthStore().reset()
    const current = router.currentRoute.value
    if (current.path.startsWith('/admin') && current.name !== 'login') {
      void router.push({ name: 'login', query: { redirect: current.fullPath } })
    }
  }

  return apiError
}

function toApiError(error: unknown): ApiError {
  if (error instanceof ApiError) return error
  return new ApiError('server', error instanceof Error ? error.message : 'Неизвестная ошибка')
}
