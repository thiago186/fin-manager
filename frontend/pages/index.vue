<template>
  <div class="min-h-screen bg-gray-50 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
    <div class="max-w-md w-full space-y-8">
      <div class="text-center">
        <h1 class="text-4xl font-bold text-gray-900 mb-2">Finance Manager</h1>
        <p class="text-gray-600">Your personal finance tracking solution</p>
      </div>

      <!-- Show different content based on authentication status -->
      <div v-if="isAuthenticated" class="bg-white shadow rounded-lg p-6">
        <div class="text-center">
          <div class="mx-auto h-12 w-12 bg-green-100 rounded-full flex items-center justify-center mb-4">
            <svg class="h-6 w-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
            </svg>
          </div>
          <h2 class="text-xl font-semibold text-gray-900 mb-2">Welcome back!</h2>
          <p class="text-gray-600 mb-6">You are successfully logged in.</p>
          <NuxtLink
            to="/transactions"
            class="w-full bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md transition-colors inline-block"
          >
            See your transactions
          </NuxtLink>
        </div>
      </div>

      <div v-else class="bg-white shadow rounded-lg p-6">
        <div class="text-center">
          <div class="mx-auto h-12 w-12 bg-blue-100 rounded-full flex items-center justify-center mb-4">
            <svg class="h-6 w-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"></path>
            </svg>
          </div>
          <h2 class="text-xl font-semibold text-gray-900 mb-2">Get Started</h2>
          <p class="text-gray-600 mb-6">Please log in to access your finance dashboard.</p>
          <NuxtLink
            to="/login"
            class="w-full bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md transition-colors inline-block"
          >
            Login
          </NuxtLink>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
const { isAuthenticated } = useAuth()
</script>