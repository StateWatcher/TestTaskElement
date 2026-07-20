/** Контракт границы: доменные операции и нормализованная ошибка.
 *
 * `ApiClient` абстрагирует именно операции, а не HTTP-запросы. Обобщённый
 * `request(url, opts)` протащил бы ресурсно-глагольную семантику REST наружу
 * и сделал бы RPC-реализацию кривой. Новая операция = метод здесь + по одной
 * реализации в каждом клиенте (фронтовый аналог «сервис + две привязки» на бэкенде).
 */

import type {
  Application,
  ApplicationInput,
  ApplicationQuery,
  ApplicationStatus,
  Booking,
  BookingInput,
  BookingQuery,
  FeedUploadResult,
  Lot,
  LotQuery,
  LotSet,
  Page,
  PageQuery,
  Session,
} from '@/domain'

export const TRANSPORTS = ['rest', 'rpc'] as const
export type Transport = (typeof TRANSPORTS)[number]

export const TRANSPORT_LABELS: Record<Transport, string> = {
  rest: 'REST',
  rpc: 'JSON-RPC',
}

/** Таксономия ошибок, одинаковая для обоих транспортов: REST выводит её из
 *  HTTP-статуса, RPC — из кода в теле 200-ответа. `network` добавлен к доменным
 *  видам, чтобы сбою самого fetch было куда лечь. */
export type ApiErrorKind =
  | 'validation'
  | 'notFound'
  | 'conflict'
  | 'unauthorized'
  | 'server'
  | 'network'

export class ApiError extends Error {
  constructor(
    readonly kind: ApiErrorKind,
    message: string,
    /** Доменный код бэкенда: lot_not_available, set_not_found, … */
    readonly code?: string,
    readonly details?: unknown,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

export interface ApiClient {
  lots: {
    list(query: LotQuery): Promise<Page<Lot>>
    get(id: number): Promise<Lot>
    projects(): Promise<string[]>
  }
  bookings: {
    create(input: BookingInput): Promise<Booking>
    list(query: BookingQuery): Promise<Page<Booking>>
    cancel(id: number): Promise<Booking>
  }
  applications: {
    create(input: ApplicationInput): Promise<Application>
    list(query: ApplicationQuery): Promise<Page<Application>>
    setStatus(id: number, status: ApplicationStatus): Promise<Application>
  }
  sets: {
    upload(file: File): Promise<FeedUploadResult>
    list(query: PageQuery): Promise<Page<LotSet>>
    activate(id: number): Promise<LotSet>
  }
  auth: {
    login(login: string, password: string): Promise<Session>
    logout(): Promise<void>
    me(): Promise<Session>
  }
}
