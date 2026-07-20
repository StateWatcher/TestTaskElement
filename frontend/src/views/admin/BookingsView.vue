<script setup lang="ts">
/** Отмена возвращает лот в продажу — это правило бэкенда, здесь только кнопка. */
import { onMounted, ref, watch } from 'vue'

import AppPagination from '@/components/AppPagination.vue'
import LotStatusBadge from '@/components/LotStatusBadge.vue'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  BOOKING_STATUSES,
  BOOKING_STATUS_LABELS,
  type BookingQuery,
  type BookingStatus,
} from '@/domain'
import { formatDateTime } from '@/lib/format'
import { useBookingsStore } from '@/stores/bookings'
import { useTransportStore } from '@/stores/transport'

const ANY = '__any__'

const bookings = useBookingsStore()
const transportStore = useTransportStore()

const query = ref<BookingQuery>({ page: 1, pageSize: 20 })

function setStatus(value: string): void {
  query.value = {
    ...query.value,
    status: value === ANY ? undefined : (value as BookingStatus),
    page: 1,
  }
}

function reload(): void {
  void bookings.fetchPage(query.value)
}

onMounted(reload)
watch(query, reload)
watch(() => transportStore.transport, reload)
</script>

<template>
  <Card>
    <CardHeader class="flex flex-wrap items-end justify-between gap-4">
      <CardTitle>Брони</CardTitle>
      <div class="space-y-2">
        <Label>Статус</Label>
        <Select :model-value="query.status ?? ANY" @update:model-value="setStatus(String($event))">
          <SelectTrigger class="w-45"><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem :value="ANY">Все</SelectItem>
            <SelectItem v-for="status in BOOKING_STATUSES" :key="status" :value="status">
              {{ BOOKING_STATUS_LABELS[status] }}
            </SelectItem>
          </SelectContent>
        </Select>
      </div>
    </CardHeader>

    <CardContent class="space-y-4">
      <Skeleton v-if="bookings.loading" class="h-[55vh] w-full" />

      <p
        v-else-if="bookings.page.items.length === 0"
        class="text-muted-foreground py-6 text-center"
      >
        Броней пока нет.
      </p>

      <template v-else>
        <Table container-class="h-[55vh] overflow-y-auto">
          <TableHeader>
            <TableRow>
              <TableHead class="bg-card sticky top-0 z-10">ID</TableHead>
              <TableHead class="bg-card sticky top-0 z-10">Лот</TableHead>
              <TableHead class="bg-card sticky top-0 z-10">Имя</TableHead>
              <TableHead class="bg-card sticky top-0 z-10">Контакт</TableHead>
              <TableHead class="bg-card sticky top-0 z-10">Создана</TableHead>
              <TableHead class="bg-card sticky top-0 z-10">Статус</TableHead>
              <TableHead class="bg-card sticky top-0 z-10" />
            </TableRow>
          </TableHeader>
          <TableBody>
            <TableRow v-for="booking in bookings.page.items" :key="booking.id">
              <TableCell>{{ booking.id }}</TableCell>
              <TableCell>
                <template v-if="booking.lot">
                  <div class="font-medium">{{ booking.lot.project }}</div>
                  <div class="text-muted-foreground text-sm">
                    №{{ booking.lot.externalId }} ·
                    <LotStatusBadge :status="booking.lot.status" />
                  </div>
                </template>
                <template v-else>#{{ booking.lotId }}</template>
              </TableCell>
              <TableCell>{{ booking.name }}</TableCell>
              <TableCell>{{ booking.contact }}</TableCell>
              <TableCell>{{ formatDateTime(booking.createdAt) }}</TableCell>
              <TableCell>
                <Badge :variant="booking.status === 'active' ? 'default' : 'outline'">
                  {{ BOOKING_STATUS_LABELS[booking.status] }}
                </Badge>
              </TableCell>
              <TableCell class="text-right">
                <Button
                  v-if="booking.status === 'active'"
                  variant="outline"
                  size="sm"
                  @click="bookings.cancel(booking.id)"
                >
                  Отменить
                </Button>
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>

        <AppPagination
          :page="bookings.page.page"
          :total="bookings.page.total"
          :page-size="bookings.page.pageSize"
          @update:page="query = { ...query, page: $event }"
        />
      </template>
    </CardContent>
  </Card>
</template>
