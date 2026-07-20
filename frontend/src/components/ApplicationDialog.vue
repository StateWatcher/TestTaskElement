<script setup lang="ts">
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
import { applicationFormSchema, fieldErrors, type FieldErrors } from '@/lib/validation'
import { useApplicationsStore } from '@/stores/applications'

const props = defineProps<{ lot?: Lot }>()
const open = defineModel<boolean>('open', { required: true })

const applications = useApplicationsStore()

type ApplicationForm = { name: string; contact: string; comment: string }

const form = ref<ApplicationForm>({ name: '', contact: '', comment: '' })
const errors = ref<FieldErrors<ApplicationForm>>({})
const pending = ref(false)

async function submit(): Promise<void> {
  const parsed = applicationFormSchema.safeParse(form.value)
  if (!parsed.success) {
    errors.value = fieldErrors(parsed.error)
    return
  }
  errors.value = {}

  pending.value = true
  try {
    await applications.create({ lotId: props.lot?.id, ...parsed.data })
    toast.success('Заявка отправлена', { description: 'Менеджер свяжется с вами' })
    open.value = false
    form.value = { name: '', contact: '', comment: '' }
  } catch (error) {
    notifyApiError(error)
  } finally {
    pending.value = false
  }
}
</script>

<template>
  <Dialog v-model:open="open">
    <DialogContent>
      <DialogHeader>
        <DialogTitle>Заявка</DialogTitle>
        <DialogDescription>
          <template v-if="lot">{{ lot.project }}, {{ lot.address }}</template>
          <template v-else>Опишите, что вас интересует</template>
        </DialogDescription>
      </DialogHeader>

      <form class="space-y-4" @submit.prevent="submit">
        <div class="space-y-2">
          <Label for="application-name">Имя</Label>
          <Input id="application-name" v-model="form.name" autocomplete="name" />
          <p v-if="errors.name" class="text-destructive text-sm">{{ errors.name }}</p>
        </div>
        <div class="space-y-2">
          <Label for="application-contact">Телефон или почта</Label>
          <Input id="application-contact" v-model="form.contact" autocomplete="tel" />
          <p v-if="errors.contact" class="text-destructive text-sm">{{ errors.contact }}</p>
        </div>
        <div class="space-y-2">
          <Label for="application-comment">Комментарий</Label>
          <textarea
            id="application-comment"
            v-model="form.comment"
            rows="4"
            class="border-input bg-transparent placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-ring/50 flex w-full rounded-md border px-3 py-2 text-sm shadow-xs focus-visible:ring-[3px] focus-visible:outline-none"
          />
          <p v-if="errors.comment" class="text-destructive text-sm">{{ errors.comment }}</p>
        </div>

        <DialogFooter>
          <Button type="button" variant="ghost" @click="open = false">Отмена</Button>
          <Button type="submit" :disabled="pending" data-testid="application-submit">
            {{ pending ? 'Отправляем…' : 'Отправить' }}
          </Button>
        </DialogFooter>
      </form>
    </DialogContent>
  </Dialog>
</template>
