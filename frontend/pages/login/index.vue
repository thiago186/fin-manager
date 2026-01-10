<template>
    <div class="min-h-screen flex items-center justify-center bg-gray-50">
      <form @submit.prevent="onSubmit" class="p-6 bg-white rounded-lg shadow-md w-full max-w-sm">
        <h1 class="text-2xl mb-4 text-center">Login</h1>
  
        <div class="mb-4">
          <label class="block mb-1">Username</label>
          <input
            v-model="username"
            type="text"
            required
            class="w-full border px-3 py-2 rounded"
          />
        </div>
  
        <div class="mb-4">
          <label class="block mb-1">Senha</label>
          <input
            v-model="password"
            type="password"
            required
            class="w-full border px-3 py-2 rounded"
          />
        </div>
  
        <div v-if="auth.error" class="mb-4 text-red-600">
          {{ auth.error }}
        </div>
  
        <button
          :disabled="loading"
          type="submit"
          class="w-full py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
        >
          {{ loading ? 'Entrando...' : 'Entrar' }}
        </button>
      </form>
    </div>
  </template>
  
  <script setup lang="ts">
  
  const username = ref<string>('')
const password = ref<string>('')
const loading = ref<boolean>(false)

const auth = useAuth()

const onSubmit = async () => {
  loading.value = true
  await auth.login(username.value, password.value)
  loading.value = false
}
  </script>