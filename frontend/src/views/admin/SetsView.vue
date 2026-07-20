<script setup lang="ts">
/** Загрузка фида и выбор активного набора.
 *
 * Наборы immutable: повторная загрузка создаёт новый набор, поэтому «обновить лоты» —
 * это загрузить фид заново и активировать свежий набор. Активен всегда ровно один,
 * и именно он виден публичной витрине. */
import { onMounted, ref, watch } from 'vue'
import { toast } from 'vue-sonner'

import AppPagination from '@/components/AppPagination.vue'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import type { PageQuery } from '@/domain'
import { formatDateTime } from '@/lib/format'
import { useSetsStore } from '@/stores/sets'
import { useTransportStore } from '@/stores/transport'

const sets = useSetsStore()
const transportStore = useTransportStore()

const file = ref<File | null>(null)
const query = ref<PageQuery>({ page: 1, pageSize: 20 })

function reload(): void {
  void sets.fetchPage(query.value)
}

function pick(event: Event): void {
  file.value = (event.target as HTMLInputElement).files?.[0] ?? null
}

async function upload(): Promise<void> {
  if (!file.value) return
  const result = await sets.upload(file.value)
  if (result) {
    toast.success(`Загружено лотов: ${result.set.lotsCount}`, {
      description: result.skipped
        ? `Пропущено записей фида: ${result.skipped}`
        : 'Все записи фида разобраны',
    })
    // новый набор сортируется первым, иначе с другой страницы его не увидеть
    query.value = { ...query.value, page: 1 }
  }
}

/** Активировать можно и исторический набор с дальней страницы — остаёмся на ней. */
async function activate(id: number): Promise<void> {
  if (await sets.activate(id)) reload()
}

onMounted(reload)
watch(query, reload)
watch(() => transportStore.transport, reload)
</script>

<template>
  <div class="space-y-6">
    <Card>
      <CardHeader>
        <CardTitle>Загрузка фида</CardTitle>
      </CardHeader>
      <CardContent class="space-y-4">
        <div class="space-y-2">
          <Label for="feed">XML-файл фида</Label>
          <Input
            id="feed"
            type="file"
            accept=".xml,text/xml"
            data-testid="feed-input"
            @change="pick"
          />
        </div>
        <Button :disabled="!file || sets.uploading" data-testid="feed-upload" @click="upload">
          {{ sets.uploading ? 'Загружаем…' : 'Загрузить' }}
        </Button>
      </CardContent>
    </Card>

    <Card>
      <CardHeader>
        <CardTitle>Наборы лотов</CardTitle>
      </CardHeader>
      <CardContent>
        <Skeleton v-if="sets.loading" class="h-[55vh] w-full" />

        <Alert v-else-if="sets.page.items.length === 0">
          <AlertTitle>Наборов пока нет</AlertTitle>
          <AlertDescription>
            Загрузите фид — публичная витрина покажет лоты только после активации набора.
          </AlertDescription>
        </Alert>

        <template v-else>
          <Table container-class="h-[55vh] overflow-y-auto">
            <TableHeader>
              <TableRow>
                <TableHead class="bg-card sticky top-0 z-10">ID</TableHead>
                <TableHead class="bg-card sticky top-0 z-10">Файл</TableHead>
                <TableHead class="bg-card sticky top-0 z-10">Загружен</TableHead>
                <TableHead class="bg-card sticky top-0 z-10">Лотов</TableHead>
                <TableHead class="bg-card sticky top-0 z-10" />
              </TableRow>
            </TableHeader>
            <TableBody>
              <TableRow v-for="lotSet in sets.page.items" :key="lotSet.id" data-testid="set-row">
                <TableCell>{{ lotSet.id }}</TableCell>
                <TableCell class="font-medium">{{ lotSet.name }}</TableCell>
                <TableCell>{{ formatDateTime(lotSet.uploadedAt) }}</TableCell>
                <TableCell>{{ lotSet.lotsCount }}</TableCell>
                <TableCell class="text-right">
                  <Badge v-if="lotSet.isActive">Активный</Badge>
                  <Button
                    v-else
                    variant="outline"
                    size="sm"
                    data-testid="activate-set"
                    @click="activate(lotSet.id)"
                  >
                    Сделать активным
                  </Button>
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>

          <AppPagination
            :page="sets.page.page"
            :total="sets.page.total"
            :page-size="sets.page.pageSize"
            @update:page="query = { ...query, page: $event }"
          />
        </template>
      </CardContent>
    </Card>
  </div>
</template>
