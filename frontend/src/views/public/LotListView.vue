<script setup lang="ts">
import { computed, onMounted, watch } from 'vue'
import { RouterLink } from 'vue-router'

import AppPagination from '@/components/AppPagination.vue'
import LotStatusBadge from '@/components/LotStatusBadge.vue'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
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
import { ToggleGroup, ToggleGroupItem } from '@/components/ui/toggle-group'
import { useLotFilters } from '@/composables/useLotFilters'
import { LOT_STATUSES, LOT_STATUS_LABELS, type LotSortField, type LotStatus } from '@/domain'
import { formatArea, formatMoney, formatRooms } from '@/lib/format'
import { useLotsStore } from '@/stores/lots'
import { useTransportStore } from '@/stores/transport'

/** shadcn/reka Select не умеет пустое значение пункта — нужен явный «любой». */
const ANY = '__any__'

const ROOM_OPTIONS = [0, 1, 2, 3, 4]
const SORT_OPTIONS: { value: LotSortField; label: string }[] = [
  { value: 'price', label: 'Цена' },
  { value: 'price_per_m2', label: 'Цена за м²' },
  { value: 'area', label: 'Площадь' },
  { value: 'floor', label: 'Этаж' },
  { value: 'rooms', label: 'Комнатность' },
]

const lots = useLotsStore()
const transportStore = useTransportStore()
const { query, update, reset } = useLotFilters()

const selectedRooms = computed(() => (query.value.rooms ?? []).map(String))
const hasFilters = computed(
  () =>
    Boolean(query.value.project) ||
    Boolean(query.value.rooms?.length) ||
    query.value.priceM2Min !== undefined ||
    query.value.priceM2Max !== undefined ||
    Boolean(query.value.status),
)

function setPrice(bound: 'priceM2Min' | 'priceM2Max', raw: string): void {
  const value = raw === '' ? undefined : Number(raw)
  update({ [bound]: Number.isFinite(value) ? value : undefined })
}

function reload(): void {
  void lots.fetchPage(query.value)
}

onMounted(() => {
  reload()
  void lots.fetchProjects()
})

watch(query, reload)

// смена транспорта перезапрашивает текущий экран: ответ обязан совпасть с прежним
watch(
  () => transportStore.transport,
  () => {
    reload()
    void lots.fetchProjects()
  },
)
</script>

<template>
  <div class="space-y-6">
    <Card>
      <CardContent class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div class="space-y-2">
          <Label>ЖК</Label>
          <Select
            :model-value="query.project ?? ANY"
            @update:model-value="update({ project: $event === ANY ? undefined : String($event) })"
          >
            <SelectTrigger class="w-full"><SelectValue placeholder="Любой" /></SelectTrigger>
            <SelectContent>
              <SelectItem :value="ANY">Любой</SelectItem>
              <SelectItem v-for="project in lots.projects" :key="project" :value="project">
                {{ project }}
              </SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div class="space-y-2">
          <Label>Статус</Label>
          <Select
            :model-value="query.status ?? ANY"
            @update:model-value="
              update({ status: $event === ANY ? undefined : ($event as LotStatus) })
            "
          >
            <SelectTrigger class="w-full"><SelectValue placeholder="Любой" /></SelectTrigger>
            <SelectContent>
              <SelectItem :value="ANY">Любой</SelectItem>
              <SelectItem v-for="status in LOT_STATUSES" :key="status" :value="status">
                {{ LOT_STATUS_LABELS[status] }}
              </SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div class="space-y-2">
          <Label>Цена за м², ₽</Label>
          <div class="flex items-center gap-2">
            <Input
              type="number"
              min="0"
              placeholder="от"
              :model-value="query.priceM2Min ?? ''"
              @change="setPrice('priceM2Min', ($event.target as HTMLInputElement).value)"
            />
            <Input
              type="number"
              min="0"
              placeholder="до"
              :model-value="query.priceM2Max ?? ''"
              @change="setPrice('priceM2Max', ($event.target as HTMLInputElement).value)"
            />
          </div>
        </div>

        <div class="space-y-2">
          <Label>Сортировка</Label>
          <div class="flex items-center gap-2">
            <Select
              :model-value="query.sort"
              @update:model-value="update({ sort: $event as LotSortField })"
            >
              <SelectTrigger class="w-full"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem
                  v-for="option in SORT_OPTIONS"
                  :key="option.value"
                  :value="option.value"
                >
                  {{ option.label }}
                </SelectItem>
              </SelectContent>
            </Select>
            <Button
              variant="outline"
              size="icon"
              :title="query.order === 'asc' ? 'По возрастанию' : 'По убыванию'"
              @click="update({ order: query.order === 'asc' ? 'desc' : 'asc' })"
            >
              {{ query.order === 'asc' ? '↑' : '↓' }}
            </Button>
          </div>
        </div>

        <div class="space-y-2 sm:col-span-2 lg:col-span-4">
          <Label>Комнатность</Label>
          <div class="flex flex-wrap items-center gap-3">
            <ToggleGroup
              type="multiple"
              variant="outline"
              :model-value="selectedRooms"
              @update:model-value="update({ rooms: (($event as string[]) ?? []).map(Number) })"
            >
              <ToggleGroupItem v-for="rooms in ROOM_OPTIONS" :key="rooms" :value="String(rooms)">
                {{ rooms === 0 ? 'Студия' : rooms }}
              </ToggleGroupItem>
            </ToggleGroup>
            <Button v-if="hasFilters" variant="ghost" size="sm" @click="reset()">
              Сбросить фильтры
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>

    <div v-if="lots.loading" class="space-y-2">
      <Skeleton v-for="row in 8" :key="row" class="h-12 w-full" />
    </div>

    <Card v-else-if="lots.page.items.length === 0">
      <CardContent class="text-muted-foreground py-10 text-center">
        <p v-if="hasFilters">Под фильтры не подошёл ни один лот.</p>
        <p v-else>
          Каталог пуст: активный набор не выбран. Загрузите фид в админке и активируйте набор.
        </p>
      </CardContent>
    </Card>

    <template v-else>
      <p class="text-muted-foreground text-sm">Найдено лотов: {{ lots.page.total }}</p>

      <Card class="py-0">
        <Table container-class="h-[55vh] overflow-y-auto">
          <TableHeader>
            <TableRow>
              <TableHead class="bg-card sticky top-0 z-10">ЖК</TableHead>
              <TableHead class="bg-card sticky top-0 z-10">Адрес</TableHead>
              <TableHead class="bg-card sticky top-0 z-10">Комнат</TableHead>
              <TableHead class="bg-card sticky top-0 z-10">Площадь</TableHead>
              <TableHead class="bg-card sticky top-0 z-10">Этаж</TableHead>
              <TableHead class="bg-card sticky top-0 z-10">Цена</TableHead>
              <TableHead class="bg-card sticky top-0 z-10">Цена за м²</TableHead>
              <TableHead class="bg-card sticky top-0 z-10">Статус</TableHead>
              <TableHead class="bg-card sticky top-0 z-10" />
            </TableRow>
          </TableHeader>
          <TableBody>
            <TableRow v-for="lot in lots.page.items" :key="lot.id" data-testid="lot-row">
              <TableCell class="font-medium">{{ lot.project }}</TableCell>
              <TableCell class="text-muted-foreground">{{ lot.address }}</TableCell>
              <TableCell>{{ formatRooms(lot.rooms) }}</TableCell>
              <TableCell>{{ formatArea(lot.area) }}</TableCell>
              <TableCell>{{ lot.floor }}</TableCell>
              <TableCell>{{ formatMoney(lot.price) }}</TableCell>
              <TableCell>{{ formatMoney(lot.pricePerM2) }}</TableCell>
              <TableCell><LotStatusBadge :status="lot.status" /></TableCell>
              <TableCell>
                <RouterLink :to="{ name: 'lot', params: { id: lot.id } }">
                  <Button variant="ghost" size="sm">Открыть</Button>
                </RouterLink>
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </Card>

      <AppPagination
        :page="lots.page.page"
        :total="lots.page.total"
        :page-size="lots.page.pageSize"
        @update:page="update({ page: $event })"
      />
    </template>
  </div>
</template>
