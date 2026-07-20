<script setup lang="ts">
import { computed } from 'vue'

import { Badge } from '@/components/ui/badge'
import { LOT_STATUS_LABELS, type LotStatus } from '@/domain'

const VARIANTS = {
  in_sale: 'default',
  booked: 'secondary',
  sold: 'outline',
} as const satisfies Record<LotStatus, string>

const props = defineProps<{ status: LotStatus }>()

const variant = computed(() => VARIANTS[props.status])
</script>

<template>
  <Badge :variant="variant" :data-status="status">{{ LOT_STATUS_LABELS[status] }}</Badge>
</template>
