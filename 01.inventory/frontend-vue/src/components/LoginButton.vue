<template>
  <div>
    <button v-if="!isLoggedIn" class="btn-start" @click="handleLogin">
      <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
        <circle cx="8" cy="8" r="7" stroke="currentColor" stroke-width="1.5"/>
        <path d="M5.5 8h5M8 5.5L10.5 8 8 10.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
      조회 시작
    </button>
    <div v-else class="login-info">
      <span>{{ userName }}</span>
      <button class="btn-logout" @click="handleLogout">로그아웃</button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';

const props = defineProps({
  tenantId:     { type: String, required: true },
  clientId:     { type: String, required: true },
  clientSecret: { type: String, required: true },
  subscriptionId: { type: String, required: true },
  redirectUri:  { type: String, default: '' },
});

const emit = defineEmits(['login', 'logout']);
const isLoggedIn = ref(false);
const userName   = ref('서비스 프린시플');

async function handleLogin() {
  if (!props.tenantId || !props.clientId || !props.clientSecret || !props.subscriptionId) {
    alert('모든 인증 정보를 입력해주세요.'); return;
  }
  isLoggedIn.value = true;
  emit('login', { name: userName.value });
}

async function handleLogout() {
  isLoggedIn.value = false;
  emit('logout');
}
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+KR:wght@400;500&display=swap');

.btn-start {
  display: inline-flex; align-items: center; gap: 8px;
  width: 100%;
  justify-content: center;
  background: linear-gradient(135deg, #1d4ed8, #2563eb);
  border: 1px solid rgba(99,179,237,0.3);
  color: #fff; border-radius: 10px;
  padding: 12px 24px; font-size: 0.95rem; font-weight: 500;
  cursor: pointer; font-family: 'IBM Plex Sans KR', sans-serif;
  transition: all 0.2s;
  box-shadow: 0 0 24px rgba(37,99,235,0.3);
}
.btn-start:hover {
  background: linear-gradient(135deg, #1e40af, #1d4ed8);
  box-shadow: 0 0 36px rgba(37,99,235,0.45);
  transform: translateY(-1px);
}

.login-info {
  display: flex; align-items: center; justify-content: center; gap: 12px;
  color: #64748b; font-size: 0.88rem;
}
.btn-logout {
  background: transparent; border: 1px solid rgba(248,113,113,0.3);
  color: #f87171; border-radius: 6px; padding: 4px 12px;
  font-size: 0.82rem; cursor: pointer; font-family: 'IBM Plex Sans KR', sans-serif;
  transition: all 0.2s;
}
.btn-logout:hover { background: rgba(248,113,113,0.1); border-color: #f87171; }
</style>