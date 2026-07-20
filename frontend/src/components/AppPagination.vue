<script setup lang="ts">
/** Обёртка над примитивами shadcn: страницы у нас всегда в форме Page<T>,
 *  и повторять эту разводку в четырёх экранах смысла нет. */
import {
  Pagination,
  PaginationContent,
  PaginationEllipsis,
  PaginationItem,
  PaginationNext,
  PaginationPrevious,
} from '@/components/ui/pagination'

defineProps<{ page: number; total: number; pageSize: number }>()
const emit = defineEmits<{ 'update:page': [value: number] }>()
</script>

<template>
  <Pagination
    v-if="total > pageSize"
    :page="page"
    :total="total"
    :items-per-page="pageSize"
    :sibling-count="1"
    show-edges
    @update:page="emit('update:page', $event)"
  >
    <PaginationContent v-slot="{ items }">
      <PaginationPrevious />
      <template v-for="(item, index) in items">
        <PaginationItem
          v-if="item.type === 'page'"
          :key="`page-${item.value}`"
          :value="item.value"
          :is-active="item.value === page"
        >
          {{ item.value }}
        </PaginationItem>
        <PaginationEllipsis v-else :key="`ellipsis-${index}`" :index="index" />
      </template>
      <PaginationNext />
    </PaginationContent>
  </Pagination>
</template>
