/** Набор лотов — результат одной загрузки фида. Наборы immutable,
 *  публично виден только активный. */

export interface LotSet {
  id: number
  name: string
  uploadedAt: Date
  lotsCount: number
  isActive: boolean
}

export interface FeedUploadResult {
  set: LotSet
  /** Лоты фида, не прошедшие разбор — импорт из-за них не падает */
  skipped: number
}
