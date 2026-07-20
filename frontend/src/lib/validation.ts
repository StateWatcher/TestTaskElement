/** Схемы форм повторяют лимиты бэкенда (`BookingCreate` / `RequestCreate`):
 *  валидируем на месте, чтобы не гонять заведомо плохой запрос, но бэкенд
 *  остаётся источником правды — его 422 всё равно нормализуется в ApiError. */

import { z } from 'zod'

const name = z.string().trim().min(1, 'Укажите имя').max(200, 'Не длиннее 200 символов')

const contact = z
  .string()
  .trim()
  .min(3, 'Укажите телефон или почту')
  .max(200, 'Не длиннее 200 символов')

const comment = z
  .string()
  .trim()
  .min(1, 'Напишите комментарий')
  .max(5000, 'Не длиннее 5000 символов')

export const bookingFormSchema = z.object({ name, contact })
export const applicationFormSchema = z.object({ name, contact, comment })

export type FieldErrors<T> = Partial<Record<keyof T, string>>

/** Первое сообщение на поле — большего форме этого размера не нужно. */
export function fieldErrors<T extends object>(error: z.ZodError<T>): FieldErrors<T> {
  const result: FieldErrors<T> = {}
  for (const issue of error.issues) {
    const field = issue.path[0] as keyof T | undefined
    if (field !== undefined && result[field] === undefined) {
      result[field] = issue.message
    }
  }
  return result
}
