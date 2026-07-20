<script setup lang="ts">
/** Переключатель транспорта — требование задания и причина существования слоя api/.
 *  Меняет только то, каким конвертом уедет следующий вызов: экраны, сторы и домен
 *  о транспорте не знают. */
import { TRANSPORT_LABELS, TRANSPORTS, type Transport } from '@/api/types'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { useTransportStore } from '@/stores/transport'

const transportStore = useTransportStore()
</script>

<template>
  <div class="flex items-center gap-2">
    <span class="text-muted-foreground hidden text-sm sm:inline">Транспорт</span>
    <Select
      :model-value="transportStore.transport"
      @update:model-value="transportStore.transport = $event as Transport"
    >
      <SelectTrigger class="w-35" data-testid="transport-switch">
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        <SelectItem v-for="value in TRANSPORTS" :key="value" :value="value">
          {{ TRANSPORT_LABELS[value] }}
        </SelectItem>
      </SelectContent>
    </Select>
  </div>
</template>
