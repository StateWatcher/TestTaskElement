/** Общий рантайм fetch-методов сторов: значение + loading + защита от гонки ответов.
 *
 * Вьюхи перезапрашивают данные через `watch` на смену транспорта и на фильтры, не отменяя
 * предыдущий запрос — `fetch` спрятан внутри `api()`, прокидывать `AbortSignal` через оба
 * транспорта усложнило бы `ApiClient` ради одного частного случая. Вместо этого — счётчик
 * поколений: ответ запроса, переставшего быть последним, отбрасывается и не перезаписывает
 * состояние поверх уже пришедшего более свежего ответа.
 */

import { ref, type Ref } from 'vue'

import { notifyApiError } from '@/lib/notify'

export interface AsyncResource<T> {
  data: Ref<T>
  loading: Ref<boolean>
  run(fetcher: () => Promise<T>, fallback: (error: unknown) => T): Promise<void>
}

export function useAsyncResource<T>(initial: T, trackLoading = true): AsyncResource<T> {
  const data = ref(initial) as Ref<T>
  const loading = ref(false)
  let generation = 0

  async function run(fetcher: () => Promise<T>, fallback: (error: unknown) => T): Promise<void> {
    const token = ++generation
    if (trackLoading) loading.value = true
    try {
      const value = await fetcher()
      if (token !== generation) return
      data.value = value
    } catch (error) {
      if (token !== generation) return
      notifyApiError(error)
      data.value = fallback(error)
    } finally {
      if (token === generation && trackLoading) loading.value = false
    }
  }

  return { data, loading, run }
}
