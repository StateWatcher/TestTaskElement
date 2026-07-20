/** Сессия админа. Токен живёт в HttpOnly-cookie и фронту не виден —
 *  здесь только то, что бэкенд отдаёт в теле ответа. */

export interface Session {
  login: string
}
