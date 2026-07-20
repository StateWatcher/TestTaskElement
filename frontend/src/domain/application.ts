/** Заявка — мягкое обращение со свободным комментарием, лот необязателен.
 *
 * В домене называется Application, чтобы не перекрывать глобальный DOM-`Request`;
 * на транспорте это по-прежнему `/api/requests` и методы `requests.*`. */

import type { Lot } from './lot'

export const APPLICATION_STATUSES = ['new', 'in_progress', 'closed'] as const
export type ApplicationStatus = (typeof APPLICATION_STATUSES)[number]

export const APPLICATION_STATUS_LABELS: Record<ApplicationStatus, string> = {
  new: 'Новая',
  in_progress: 'В работе',
  closed: 'Закрыта',
}

export interface Application {
  id: number
  lotId: number | null
  name: string
  contact: string
  comment: string
  status: ApplicationStatus
  createdAt: Date
  lot: Lot | null
}

export interface ApplicationInput {
  lotId?: number
  name: string
  contact: string
  comment: string
}

export interface ApplicationQuery {
  status?: ApplicationStatus
  page: number
  pageSize: number
}
