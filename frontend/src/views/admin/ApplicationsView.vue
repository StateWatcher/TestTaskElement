<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'

import AppPagination from '@/components/AppPagination.vue'
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
  APPLICATION_STATUSES,
  APPLICATION_STATUS_LABELS,
  type ApplicationQuery,
  type ApplicationStatus,
} from '@/domain'
import { formatDateTime } from '@/lib/format'
import { useApplicationsStore } from '@/stores/applications'
import { useTransportStore } from '@/stores/transport'

const ANY = '__any__'

const applications = useApplicationsStore()
const transportStore = useTransportStore()

const query = ref<ApplicationQuery>({ page: 1, pageSize: 20 })

function setFilter(value: string): void {
  query.value = {
    ...query.value,
    status: value === ANY ? undefined : (value as ApplicationStatus),
    page: 1,
  }
}

function reload(): void {
  void applications.fetchPage(query.value)
}

onMounted(reload)
watch(query, reload)
watch(() => transportStore.transport, reload)
</script>

<template>
  <Card>
    <CardHeader class="flex flex-wrap items-end justify-between gap-4">
      <CardTitle>Заявки</CardTitle>
      <div class="space-y-2">
        <Label>Статус</Label>
        <Select :model-value="query.status ?? ANY" @update:model-value="setFilter(String($event))">
          <SelectTrigger class="w-45"><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem :value="ANY">Все</SelectItem>
            <SelectItem v-for="status in APPLICATION_STATUSES" :key="status" :value="status">
              {{ APPLICATION_STATUS_LABELS[status] }}
            </SelectItem>
          </SelectContent>
        </Select>
      </div>
    </CardHeader>

    <CardContent class="space-y-4">
      <Skeleton v-if="applications.loading" class="h-[55vh] w-full" />

      <p
        v-else-if="applications.page.items.length === 0"
        class="text-muted-foreground py-6 text-center"
      >
        Заявок пока нет.
      </p>

      <template v-else>
        <Table container-class="h-[55vh] overflow-y-auto">
          <TableHeader>
            <TableRow>
              <TableHead class="bg-card sticky top-0 z-10">ID</TableHead>
              <TableHead class="bg-card sticky top-0 z-10">Лот</TableHead>
              <TableHead class="bg-card sticky top-0 z-10">Имя</TableHead>
              <TableHead class="bg-card sticky top-0 z-10">Контакт</TableHead>
              <TableHead class="bg-card sticky top-0 z-10">Комментарий</TableHead>
              <TableHead class="bg-card sticky top-0 z-10">Создана</TableHead>
              <TableHead class="bg-card sticky top-0 z-10">Статус</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            <TableRow v-for="application in applications.page.items" :key="application.id">
              <TableCell>{{ application.id }}</TableCell>
              <TableCell>
                <template v-if="application.lot">
                  <div class="font-medium">{{ application.lot.project }}</div>
                  <div class="text-muted-foreground text-sm">
                    №{{ application.lot.externalId }}
                  </div>
                </template>
                <span v-else class="text-muted-foreground">без лота</span>
              </TableCell>
              <TableCell>{{ application.name }}</TableCell>
              <TableCell>{{ application.contact }}</TableCell>
              <TableCell class="max-w-xs whitespace-pre-line">{{ application.comment }}</TableCell>
              <TableCell>{{ formatDateTime(application.createdAt) }}</TableCell>
              <TableCell>
                <Select
                  :model-value="application.status"
                  @update:model-value="
                    applications.setStatus(application.id, $event as ApplicationStatus)
                  "
                >
                  <SelectTrigger class="w-37.5"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem v-for="status in APPLICATION_STATUSES" :key="status" :value="status">
                      {{ APPLICATION_STATUS_LABELS[status] }}
                    </SelectItem>
                  </SelectContent>
                </Select>
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>

        <AppPagination
          :page="applications.page.page"
          :total="applications.page.total"
          :page-size="applications.page.pageSize"
          @update:page="query = { ...query, page: $event }"
        />
      </template>
    </CardContent>
  </Card>
</template>
