<script setup lang="ts">
</script>

<template>
  <div class="min-h-screen p-6">
    <div class="max-w-7xl mx-auto">
      <h1 class="text-3xl font-bold mb-6">DNSSEC Validation</h1>

      <div class="panel">
        <p class="text-theme-dark-text-secondary">
          DNSSEC chain validation (root → TLD → domain) will appear here
        </p>
      </div>

      <div class="mt-6">
        <router-link to="/" class="text-blue-500 hover:text-blue-400">
          ← Back to Dashboard
        </router-link>
      </div>
    </div>
  </div>
</template>
