<script setup lang="ts">
import { ref } from 'vue';

const domain = ref('');
</script>

<template>
  <div class="min-h-screen p-6">
    <div class="max-w-7xl mx-auto">
      <h1 class="text-3xl font-bold mb-6">DNS Debugger</h1>

      <div class="mb-6">
        <input
          v-model="domain"
          type="text"
          placeholder="Enter domain (e.g., example.com)"
          class="w-full max-w-md px-4 py-2 bg-theme-dark-surface border border-theme-dark-border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <!-- Registration Card (full height left) -->
        <div class="card lg:row-span-2">
          <h2 class="text-xl font-semibold mb-3">Registration</h2>
          <p class="text-theme-dark-text-secondary">Domain registration information will appear here</p>
        </div>

        <!-- DNS Card -->
        <div class="card">
          <h2 class="text-xl font-semibold mb-3">DNS</h2>
          <p class="text-theme-dark-text-secondary">DNS records summary</p>
        </div>

        <!-- Email Card -->
        <div class="card">
          <h2 class="text-xl font-semibold mb-3">Email</h2>
          <p class="text-theme-dark-text-secondary">Email security status</p>
        </div>

        <!-- DNSSEC Card -->
        <div class="card">
          <h2 class="text-xl font-semibold mb-3">DNSSEC</h2>
          <p class="text-theme-dark-text-secondary">DNSSEC validation</p>
        </div>

        <!-- Certificate Card -->
        <div class="card">
          <h2 class="text-xl font-semibold mb-3">Certificate</h2>
          <p class="text-theme-dark-text-secondary">SSL/TLS certificate info</p>
        </div>

        <!-- HTTP Card -->
        <div class="card lg:col-span-2">
          <h2 class="text-xl font-semibold mb-3">HTTP/HTTPS</h2>
          <p class="text-theme-dark-text-secondary">HTTP connectivity status</p>
        </div>
      </div>

      <!-- Navigation tabs -->
      <div class="mt-6 flex gap-2">
        <router-link to="/" class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
          Dashboard
        </router-link>
        <router-link to="/registration" class="px-4 py-2 bg-theme-dark-surface border border-theme-dark-border rounded hover:bg-theme-dark-border">
          Registration
        </router-link>
        <router-link to="/dns" class="px-4 py-2 bg-theme-dark-surface border border-theme-dark-border rounded hover:bg-theme-dark-border">
          DNS
        </router-link>
        <router-link to="/dnssec" class="px-4 py-2 bg-theme-dark-surface border border-theme-dark-border rounded hover:bg-theme-dark-border">
          DNSSEC
        </router-link>
        <router-link to="/certificate" class="px-4 py-2 bg-theme-dark-surface border border-theme-dark-border rounded hover:bg-theme-dark-border">
          Certificate
        </router-link>
        <router-link to="/http" class="px-4 py-2 bg-theme-dark-surface border border-theme-dark-border rounded hover:bg-theme-dark-border">
          HTTP
        </router-link>
        <router-link to="/email" class="px-4 py-2 bg-theme-dark-surface border border-theme-dark-border rounded hover:bg-theme-dark-border">
          Email
        </router-link>
      </div>
    </div>
  </div>
</template>
