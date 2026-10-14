<script setup lang="ts">
import Toast from '@/components/common/Toast.vue'
</script>

<template>
  <div class="min-h-screen">
    <router-view />
    <Toast />
  </div>
</template>
