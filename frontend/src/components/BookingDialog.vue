<script setup lang="ts">
/** Бронь лота. Опорный кейс паритета транспортов: занятый лот даёт HTTP 409 в REST
 *  и код -32003 в JSON-RPC, а сюда в обоих случаях приходит ApiError('conflict'). */
import { ref } from 'vue'
import { toast } from 'vue-sonner'

import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import type { Lot } from '@/domain'
import { notifyApiError } from '@/lib/notify'
import { bookingFormSchema, fieldErrors, type FieldErrors } from '@/lib/validation'
import { useBookingsStore } from '@/stores/bookings'

const props = defineProps<{ lot: Lot }>()
const open = defineModel<boolean>('open', { required: true })
const emit = defineEmits<{ done: [] }>()

const bookings = useBookingsStore()

const form = ref({ name: '', contact: '' })
const errors = ref<FieldErrors<{ name: string; contact: string }>>({})
const pending = ref(false)

async function submit(): Promise<void> {
  const parsed = bookingFormSchema.safeParse(form.value)
  if (!parsed.success) {
    errors.value = fieldErrors(parsed.error)
    return
  }
  errors.value = {}

  pending.value = true
  try {
    await bookings.create({ lotId: props.lot.id, ...parsed.data })
    toast.success('Лот забронирован', { description: 'Мы свяжемся с вами по указанному контакту' })
    open.value = false
    form.value = { name: '', contact: '' }
  } catch (error) {
    // конфликт оставляет диалог открытым: статус лота уже изменился, экран его перечитает
    notifyApiError(error)
  } finally {
    pending.value = false
    emit('done')
  }
}
</script>

<template>
  <Dialog v-model:open="open">
    <DialogContent>
      <DialogHeader>
        <DialogTitle>Бронирование лота</DialogTitle>
        <DialogDescription>
          {{ lot.project }}, {{ lot.address }} — лот №{{ lot.externalId }}
        </DialogDescription>
      </DialogHeader>

      <form class="space-y-4" @submit.prevent="submit">
        <div class="space-y-2">
          <Label for="booking-name">Имя</Label>
          <Input id="booking-name" v-model="form.name" autocomplete="name" />
          <p v-if="errors.name" class="text-destructive text-sm">{{ errors.name }}</p>
        </div>
        <div class="space-y-2">
          <Label for="booking-contact">Телефон или почта</Label>
          <Input id="booking-contact" v-model="form.contact" autocomplete="tel" />
          <p v-if="errors.contact" class="text-destructive text-sm">{{ errors.contact }}</p>
        </div>

        <DialogFooter>
          <Button type="button" variant="ghost" @click="open = false">Отмена</Button>
          <Button type="submit" :disabled="pending" data-testid="booking-submit">
            {{ pending ? 'Бронируем…' : 'Забронировать' }}
          </Button>
        </DialogFooter>
      </form>
    </DialogContent>
  </Dialog>
</template>
