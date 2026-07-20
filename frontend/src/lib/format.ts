/** Форматирование чисел и дат для витрины. Числа приходят из домена уже числами. */

const money = new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 0 })
const decimal = new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 2 })
const dateTime = new Intl.DateTimeFormat('ru-RU', { dateStyle: 'short', timeStyle: 'short' })

export function formatMoney(value: number | null): string {
  return value === null ? '—' : `${money.format(value)} ₽`
}

export function formatArea(value: number): string {
  return `${decimal.format(value)} м²`
}

export function formatRooms(rooms: number): string {
  return rooms === 0 ? 'Студия' : `${rooms}-комн.`
}

export function formatDateTime(value: Date): string {
  return dateTime.format(value)
}
