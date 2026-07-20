<script setup lang="ts">
import 'vue-sonner/style.css'

import { RouterLink, RouterView, useRoute } from 'vue-router'

import TransportSwitch from '@/components/TransportSwitch.vue'
import { Button } from '@/components/ui/button'
import { Toaster } from '@/components/ui/sonner'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const route = useRoute()

const publicLinks = [{ name: 'lots', label: 'Каталог' }] as const
const adminLinks = [
  { name: 'admin-sets', label: 'Наборы' },
  { name: 'admin-bookings', label: 'Брони' },
  { name: 'admin-requests', label: 'Заявки' },
] as const

function isActive(name: string): boolean {
  return route.name === name
}
</script>

<template>
  <div class="bg-background text-foreground min-h-screen">
    <header class="border-b sticky top-0 z-40 bg-background">
      <div class="mx-auto flex max-w-7xl flex-wrap items-center gap-x-6 gap-y-3 px-4 py-3">
        <RouterLink :to="{ name: 'lots' }" class="font-semibold">Выборщик лотов</RouterLink>

        <nav class="flex items-center gap-1">
          <RouterLink v-for="link in publicLinks" :key="link.name" :to="{ name: link.name }">
            <Button :variant="isActive(link.name) ? 'secondary' : 'ghost'" size="sm">
              {{ link.label }}
            </Button>
          </RouterLink>
          <template v-if="auth.isAuthenticated">
            <RouterLink v-for="link in adminLinks" :key="link.name" :to="{ name: link.name }">
              <Button :variant="isActive(link.name) ? 'secondary' : 'ghost'" size="sm">
                {{ link.label }}
              </Button>
            </RouterLink>
          </template>
        </nav>

        <div class="ml-auto flex items-center gap-3">
          <TransportSwitch />
          <template v-if="auth.isAuthenticated">
            <span class="text-muted-foreground hidden text-sm sm:inline">
              {{ auth.session?.login }}
            </span>
            <Button variant="outline" size="sm" @click="auth.logout()">Выйти</Button>
          </template>
          <RouterLink v-else :to="{ name: 'login' }">
            <Button variant="outline" size="sm">Админка</Button>
          </RouterLink>
        </div>
      </div>
    </header>

    <main class="mx-auto max-w-7xl px-4 py-6">
      <RouterView />
    </main>

    <Toaster position="top-right" rich-colors />
  </div>
</template>
