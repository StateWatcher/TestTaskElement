<script setup lang="ts">
/** Карточка лота с формами брони и заявки.
 *  Бронировать можно только лот «в продаже» — то же правило проверяет бэкенд,
 *  здесь оно лишь прячет кнопку. */
import { computed, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'

import ApplicationDialog from '@/components/ApplicationDialog.vue'
import BookingDialog from '@/components/BookingDialog.vue'
import LotStatusBadge from '@/components/LotStatusBadge.vue'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import { Skeleton } from '@/components/ui/skeleton'
import { formatArea, formatDateTime, formatMoney, formatRooms } from '@/lib/format'
import { useLotsStore } from '@/stores/lots'
import { useTransportStore } from '@/stores/transport'

const props = defineProps<{ id: number }>()

const lots = useLotsStore()
const transportStore = useTransportStore()

const bookingOpen = ref(false)
const applicationOpen = ref(false)

const lot = computed(() => lots.current)
const canBook = computed(() => lot.value?.status === 'in_sale')

function reload(): void {
  void lots.fetchLot(props.id)
}

watch([() => props.id, () => transportStore.transport], reload, { immediate: true })
</script>

<template>
  <div class="space-y-4">
    <RouterLink :to="{ name: 'lots' }">
      <Button variant="ghost" size="sm">← К каталогу</Button>
    </RouterLink>

    <Skeleton v-if="lots.lotLoading" class="h-64 w-full" />

    <Card v-else-if="!lot">
      <CardContent class="text-muted-foreground py-10 text-center">
        Лот не найден: он мог быть из неактивного набора.
      </CardContent>
    </Card>

    <Card v-else>
      <CardHeader>
        <CardTitle class="flex flex-wrap items-center gap-3">
          <span>{{ lot.project }}</span>
          <LotStatusBadge :status="lot.status" />
        </CardTitle>
        <p class="text-muted-foreground text-sm">{{ lot.address }}</p>
      </CardHeader>

      <CardContent class="space-y-6">
        <dl class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div>
            <dt class="text-muted-foreground text-sm">Комнатность</dt>
            <dd class="text-lg">{{ formatRooms(lot.rooms) }}</dd>
          </div>
          <div>
            <dt class="text-muted-foreground text-sm">Площадь</dt>
            <dd class="text-lg">{{ formatArea(lot.area) }}</dd>
          </div>
          <div>
            <dt class="text-muted-foreground text-sm">Этаж</dt>
            <dd class="text-lg">{{ lot.floor }}</dd>
          </div>
          <div>
            <dt class="text-muted-foreground text-sm">Номер лота</dt>
            <dd class="text-lg">{{ lot.externalId }}</dd>
          </div>
          <div>
            <dt class="text-muted-foreground text-sm">Цена</dt>
            <dd class="text-lg font-semibold">{{ formatMoney(lot.price) }}</dd>
          </div>
          <div>
            <dt class="text-muted-foreground text-sm">Базовая цена</dt>
            <dd class="text-lg">{{ formatMoney(lot.priceBase) }}</dd>
          </div>
          <div>
            <dt class="text-muted-foreground text-sm">Цена за м²</dt>
            <dd class="text-lg">{{ formatMoney(lot.pricePerM2) }}</dd>
          </div>
          <div>
            <dt class="text-muted-foreground text-sm">Обновлён</dt>
            <dd class="text-lg">{{ formatDateTime(lot.updatedAt) }}</dd>
          </div>
        </dl>

        <Separator />

        <div class="flex flex-wrap gap-3">
          <Button v-if="canBook" data-testid="book-lot" @click="bookingOpen = true">
            Забронировать
          </Button>
          <Button v-else disabled data-testid="book-lot-disabled">
            Бронь недоступна: {{ lot.status === 'booked' ? 'лот забронирован' : 'лот продан' }}
          </Button>
          <Button
            variant="outline"
            data-testid="create-application"
            @click="applicationOpen = true"
          >
            Оставить заявку
          </Button>
        </div>
      </CardContent>
    </Card>

    <BookingDialog v-if="lot" v-model:open="bookingOpen" :lot="lot" @done="reload()" />
    <ApplicationDialog v-if="lot" v-model:open="applicationOpen" :lot="lot" />
  </div>
</template>
