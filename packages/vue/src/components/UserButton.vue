<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useDeskId } from '../context'

const deskId = useDeskId()
const isOpen = ref(false)
const dropdownRef = ref<HTMLElement | null>(null)

function toggle() {
  isOpen.value = !isOpen.value
}

function close() {
  isOpen.value = false
}

function handleClickOutside(event: MouseEvent) {
  if (dropdownRef.value && !dropdownRef.value.contains(event.target as Node)) {
    close()
  }
}

async function handleSwitchOrg(orgId: string) {
  await deskId.switchOrg(orgId)
  close()
}

async function handleLogout() {
  await deskId.logout()
  close()
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<template>
  <div v-if="deskId.isAuthenticated.value" class="deskid-user-menu" ref="dropdownRef">
    <button
      type="button"
      @click="toggle"
      :aria-expanded="isOpen"
      aria-haspopup="menu"
      class="deskid-avatar-btn"
    >
      <span class="deskid-avatar-initial">
        {{ (deskId.user.value?.display_name || deskId.user.value?.email || 'U').charAt(0).toUpperCase() }}
      </span>
    </button>

    <div v-if="isOpen" class="deskid-dropdown-card" role="menu">
      <div class="deskid-user-info">
        <div class="deskid-user-name">
          {{ deskId.user.value?.display_name || 'DeskID User' }}
        </div>
        <div class="deskid-user-email">
          {{ deskId.user.value?.email }}
        </div>
        <div v-if="deskId.activeOrg.value" class="deskid-org-pill">
          Tenant: {{ deskId.activeOrg.value.name }}
        </div>
      </div>

      <!-- Multiple Orgs switcher if present -->
      <div v-if="deskId.user.value?.orgs && deskId.user.value.orgs.length > 1" class="deskid-org-list">
        <div class="deskid-section-label">Switch Tenant</div>
        <button
          v-for="org in deskId.user.value.orgs"
          :key="org.id"
          type="button"
          @click="handleSwitchOrg(org.id)"
          class="deskid-org-item"
        >
          <span>{{ org.name }}</span>
          <span v-if="org.id === deskId.activeOrg.value?.id" class="deskid-check">✓</span>
        </button>
      </div>

      <div class="deskid-menu-footer">
        <button
          type="button"
          @click="handleLogout"
          class="deskid-logout-btn"
          role="menuitem"
        >
          Sign Out
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.deskid-user-menu {
  position: relative;
  display: inline-block;
  font-family: system-ui, -apple-system, sans-serif;
}

.deskid-avatar-btn {
  width: 2rem;
  height: 2rem;
  border-radius: 9999px;
  background: linear-gradient(135deg, #4f46e5, #6366f1);
  color: #ffffff;
  border: 2px solid #e0e7ff;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  padding: 0;
  transition: transform 0.15s ease;
}

.deskid-avatar-btn:hover {
  transform: scale(1.05);
}

.deskid-avatar-initial {
  font-weight: 700;
  font-size: 0.75rem;
}

.deskid-dropdown-card {
  position: absolute;
  right: 0;
  margin-top: 0.5rem;
  width: 14rem;
  background-color: #ffffff;
  border-radius: 0.75rem;
  box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1);
  border: 1px solid #e2e8f0;
  overflow: hidden;
  z-index: 1000;
  font-size: 0.75rem;
}

.deskid-user-info {
  padding: 0.75rem;
  border-bottom: 1px solid #f1f5f9;
}

.deskid-user-name {
  font-weight: 600;
  color: #0f172a;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.deskid-user-email {
  color: #64748b;
  margin-top: 0.125rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.deskid-org-pill {
  display: inline-block;
  margin-top: 0.375rem;
  padding: 0.125rem 0.375rem;
  border-radius: 0.25rem;
  background-color: #f1f5f9;
  color: #475569;
  font-size: 0.625rem;
  font-weight: 600;
}

.deskid-org-list {
  padding: 0.375rem;
  border-bottom: 1px solid #f1f5f9;
}

.deskid-section-label {
  padding: 0.25rem 0.375rem;
  color: #94a3b8;
  font-size: 0.625rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.deskid-org-item {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.375rem;
  border-radius: 0.375rem;
  border: none;
  background: transparent;
  color: #334155;
  font-size: 0.75rem;
  cursor: pointer;
  text-align: left;
}

.deskid-org-item:hover {
  background-color: #f8fafc;
}

.deskid-check {
  color: #4f46e5;
  font-weight: 700;
}

.deskid-menu-footer {
  padding: 0.375rem;
}

.deskid-logout-btn {
  width: 100%;
  padding: 0.375rem;
  border-radius: 0.375rem;
  border: none;
  background: transparent;
  color: #e11d48;
  font-size: 0.75rem;
  font-weight: 600;
  cursor: pointer;
  text-align: left;
}

.deskid-logout-btn:hover {
  background-color: #fff1f2;
}
</style>
