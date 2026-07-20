/** Сессия админа. Токен лежит в HttpOnly-cookie и фронту не виден, поэтому стор
 *  хранит только факт авторизации: единственный способ его узнать — спросить бэкенд.
 *
 *  `checked` отличает «ещё не спрашивали» от «спросили, не авторизованы» — иначе
 *  guard роутера дёргал бы `/auth/me` на каждый переход. */

import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { api, ApiError } from '@/api'
import type { Session } from '@/domain'

export const useAuthStore = defineStore('auth', () => {
  const session = ref<Session | null>(null)
  const checked = ref(false)
  const pending = ref(false)

  const isAuthenticated = computed(() => session.value !== null)

  async function login(loginName: string, password: string): Promise<void> {
    pending.value = true
    try {
      session.value = await api().auth.login(loginName, password)
      checked.value = true
    } finally {
      pending.value = false
    }
  }

  async function logout(): Promise<void> {
    try {
      await api().auth.logout()
    } finally {
      reset()
      checked.value = true
    }
  }

  /** Возвращает true, если сессия жива. 401 — штатный ответ, не ошибка. */
  async function ensureSession(): Promise<boolean> {
    if (checked.value) return isAuthenticated.value
    try {
      session.value = await api().auth.me()
    } catch (error) {
      if (error instanceof ApiError && error.kind === 'unauthorized') {
        session.value = null
      } else {
        throw error
      }
    } finally {
      checked.value = true
    }
    return isAuthenticated.value
  }

  /** Дёргается на любой `unauthorized` от любого транспорта: сессия могла истечь. */
  function reset(): void {
    session.value = null
  }

  return { session, checked, pending, isAuthenticated, login, logout, ensureSession, reset }
})
