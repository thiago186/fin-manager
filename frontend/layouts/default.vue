<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Navigation -->
    <nav v-if="isAuthenticated" class="bg-white shadow">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between h-16">
          <div class="flex">
            <div class="flex-shrink-0 flex items-center">
              <h1 class="text-xl font-bold text-gray-900">Finance Manager</h1>
            </div>
            <div class="hidden sm:ml-6 sm:flex sm:space-x-8">
              <NuxtLink
                to="/cash-flow"
                class="border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium"
                active-class="border-indigo-500 text-gray-900"
              >
                Fluxo de Caixa
              </NuxtLink>
              <div class="relative group inline-flex">
                <NuxtLink
                  to="/transactions"
                  class="border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium"
                  active-class="border-indigo-500 text-gray-900"
                >
                  Transações
                </NuxtLink>
                <div
                  class="absolute left-0 top-full z-20 hidden min-w-[180px] rounded-md border border-gray-200 bg-white py-1 shadow-lg group-hover:block group-focus-within:block"
                >
                  <NuxtLink
                    to="/transactions/duplicates"
                    class="block px-4 py-2 text-sm text-gray-600 hover:bg-gray-50 hover:text-gray-900"
                    :class="route.path === '/transactions/duplicates' ? 'text-indigo-600 font-medium' : ''"
                  >
                    Duplicadas
                  </NuxtLink>
                  <NuxtLink
                    to="/installments"
                    class="block px-4 py-2 text-sm text-gray-600 hover:bg-gray-50 hover:text-gray-900"
                    :class="route.path.startsWith('/installments') ? 'text-indigo-600 font-medium' : ''"
                  >
                    Parcelamentos
                  </NuxtLink>
                </div>
              </div>
              <NuxtLink
                to="/categories"
                class="border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium"
                active-class="border-indigo-500 text-gray-900"
              >
                Categorias
              </NuxtLink>
              <NuxtLink
                to="/budgets"
                class="border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium"
                active-class="border-indigo-500 text-gray-900"
              >
                Orçamentos
              </NuxtLink>
              <NuxtLink
                to="/accounts"
                class="border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium"
                active-class="border-indigo-500 text-gray-900"
              >
                Contas
              </NuxtLink>
              <NuxtLink
                to="/credit-cards"
                class="border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium"
                active-class="border-indigo-500 text-gray-900"
              >
                Cartões
              </NuxtLink>
              <NuxtLink
                to="/settings"
                class="border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium"
                active-class="border-indigo-500 text-gray-900"
              >
                Settings
              </NuxtLink>
            </div>
          </div>
          <div class="hidden sm:ml-6 sm:flex sm:items-center">
            <div class="ml-3 relative">
              <div class="flex items-center space-x-4">
                <span class="text-sm text-gray-700">{{ user?.username }}</span>
                <Button size="sm" variant="destructive" @click="logout">
                  Logout
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </nav>

    <!-- Page Content -->
    <main>
      <slot />
    </main>
  </div>
</template>

<script setup lang="ts">
import { Button } from '@/components/ui/button'

const route = useRoute()
const { isAuthenticated, user, logout } = useAuth()
</script>
