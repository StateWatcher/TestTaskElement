# Фронтенд «Выборщика лотов»

Vue 3 + TypeScript + Vite + Tailwind, UI — shadcn-vue. Публичная витрина, админка
и переключатель транспорта REST / JSON-RPC. Общий обзор проекта и отчёт — в корневом
[README.md](../README.md).

## Команды

```sh
pnpm install
pnpm dev            # http://localhost:5173, /api проксируется на localhost:8000
pnpm build          # type-check + сборка
pnpm type-check
pnpm lint           # oxlint + eslint
pnpm test:unit      # vitest
pnpm test:e2e       # playwright, нужен поднятый стек (docker compose up)
```

Перед первым прогоном e2e: `pnpm exec playwright install chromium`.
Логин суперюзера для e2e берётся из корневого `.env` (`AUTH_SUPERUSER_*`).

## Слои

```
src/
  domain/       чистые типы (Lot, Booking, Application, LotSet, Page<T>, LotQuery)
                — ни Vue, ни fetch
  api/
    types.ts    интерфейс ApiClient и доменный ApiError
    http.ts     обёртка над fetch: baseURL, cookie-сессия, таймауты
    dto.ts      zod-схемы ответов и мапперы DTO → домен + сериализация запросов
    rest/       client.ts + errors.ts (статус → вид ошибки)
    rpc/        client.ts + errors.ts (код -32xxx → вид ошибки)
    index.ts    api() — резолвит реализацию по стору транспорта
  stores/       transport, auth, lots, bookings, applications, sets
  composables/  useLotFilters — фильтры каталога в query-строке роутера
  router/       маршруты и guard админки
  views/        public/ (LotList, LotDetail), admin/ (Login, Sets, Bookings, Applications)
  components/   свои компоненты + ui/ (shadcn-vue, копируется CLI в репозиторий)
  lib/          notify (ApiError → тост), format, validation
```

Правило границы: `views` и `stores` знают только про `ApiClient` и домен;
всё, что специфично для REST или JSON-RPC, живёт внутри `api/rest` и `api/rpc`.
