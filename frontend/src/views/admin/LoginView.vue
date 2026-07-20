<script setup lang="ts">
/** Вход суперюзера из конфига бэкенда. Регистрации нет по условию задания.
 *  Токен возвращается HttpOnly-cookie, поэтому здесь нечего сохранять. */
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { notifyApiError } from '@/lib/notify'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()

const form = ref({ login: '', password: '' })

async function submit(): Promise<void> {
  try {
    await auth.login(form.value.login, form.value.password)
    const redirect = route.query.redirect
    await router.push(typeof redirect === 'string' ? redirect : { name: 'admin-sets' })
  } catch (error) {
    notifyApiError(error)
  }
}
</script>

<template>
  <Card class="mx-auto max-w-md">
    <CardHeader>
      <CardTitle>Вход в админку</CardTitle>
    </CardHeader>
    <CardContent>
      <form class="space-y-4" @submit.prevent="submit">
        <div class="space-y-2">
          <Label for="login">Логин</Label>
          <Input id="login" v-model="form.login" autocomplete="username" required />
        </div>
        <div class="space-y-2">
          <Label for="password">Пароль</Label>
          <Input
            id="password"
            v-model="form.password"
            type="password"
            autocomplete="current-password"
            required
          />
        </div>
        <Button type="submit" class="w-full" :disabled="auth.pending" data-testid="login-submit">
          {{ auth.pending ? 'Входим…' : 'Войти' }}
        </Button>
      </form>
    </CardContent>
  </Card>
</template>
