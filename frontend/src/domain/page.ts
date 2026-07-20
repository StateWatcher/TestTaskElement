export interface Page<T> {
  items: T[]
  total: number
  page: number
  pageSize: number
}

/** Запрос страницы без фильтров: общий минимум для всех списков. */
export interface PageQuery {
  page: number
  pageSize: number
}

export function emptyPage<T>(page = 1, pageSize = 20): Page<T> {
  return { items: [], total: 0, page, pageSize }
}

export function pageCount(page: Page<unknown>): number {
  return Math.max(1, Math.ceil(page.total / page.pageSize))
}
