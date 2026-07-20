/** Выбранный транспорт. Отдельный стор, потому что от него зависит каждый вызов API,
 *  а живёт он дольше любого экрана: режим переживает перезагрузку через localStorage. */

import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

import { TRANSPORTS, type Transport } from '@/api/types'

const STORAGE_KEY = 'transport'

function restore(): Transport {
  const stored = localStorage.getItem(STORAGE_KEY)
  return TRANSPORTS.includes(stored as Transport) ? (stored as Transport) : 'rest'
}

export const useTransportStore = defineStore('transport', () => {
  const transport = ref<Transport>(restore())

  watch(transport, (value) => localStorage.setItem(STORAGE_KEY, value))

  return { transport }
})
