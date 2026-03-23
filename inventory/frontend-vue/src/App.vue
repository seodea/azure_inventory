<template>
  <div class="app">
    <!-- 배경 그리드 패턴 -->
    <div class="bg-grid"></div>

    <div class="layout">
      <!-- ── 헤더 ── -->
      <header class="topbar">
        <div class="topbar-brand">
          <span class="brand-icon">⬡</span>
          <span class="brand-name">Azure Inventory</span>
        </div>
        <div class="topbar-right" v-if="isLoggedIn">
          <span class="user-chip">
            <span class="user-dot"></span>
            {{ userName }}
          </span>
          <button class="btn-logout" @click="onLogoutClick">로그아웃</button>
        </div>
      </header>

      <!-- ── 로그인 전 ── -->
      <main v-if="!isLoggedIn" class="login-pane">
        <div class="login-card">
          <div class="login-header">
            <h1>Azure 리소스 인벤토리</h1>
            <p>Service Principal 정보를 입력하고 조회를 시작하세요.</p>
          </div>
          <div class="form-grid">
            <div class="form-field">
              <label>Tenant ID <span class="label-sub">(Directory ID)</span></label>
              <input type="password" v-model="tenantId" placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" autocomplete="off" />
            </div>
            <div class="form-field">
              <label>Client ID <span class="label-sub">(Application ID)</span></label>
              <input type="password" v-model="clientId" placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" autocomplete="off" />
            </div>
            <div class="form-field">
              <label>Client Secret</label>
              <input type="password" v-model="clientSecret" placeholder="••••••••••••••••" autocomplete="off" />
            </div>
            <div class="form-field">
              <label>Subscription ID</label>
              <input type="password" v-model="subscriptionId" placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" autocomplete="off" />
              <div class="sub-actions">
                <button class="btn-sub" type="button" @click="fetchSubscriptions" :disabled="subsLoading">
                  {{ subsLoading ? '구독 불러오는 중...' : '구독 불러오기' }}
                </button>
                <span class="sub-hint" v-if="subscriptions.length">
                  {{ subscriptions.length }}개 구독 조회됨
                </span>
              </div>
              <div class="sub-select" v-if="subscriptions.length">
                <select v-model="subscriptionId">
                  <option value="">구독 선택</option>
                  <option v-for="s in subscriptions" :key="s.subscription_id" :value="s.subscription_id">
                    {{ s.display_name || '구독' }} ({{ s.subscription_id }})
                  </option>
                </select>
              </div>
              <p class="form-error" v-if="subsError">{{ subsError }}</p>
            </div>
          </div>
          <LoginButton
            :tenant-id="tenantId"
            :client-id="clientId"
            :client-secret="clientSecret"
            :subscription-id="subscriptionId"
            @login="onLogin"
            @logout="onLogout"
          />
        </div>
      </main>

      <!-- ── 로그인 후 ── -->
      <main v-else class="dashboard">

        <!-- 리전 선택 -->
        <section class="region-section">
          <div class="section-label">
            <span class="section-dot"></span>
            리전 선택
          </div>
          <div class="region-cards">
            <button
              v-for="r in regionOptions"
              :key="r.value"
              class="region-card"
              :class="{ active: selectedRegion === r.value }"
              @click="selectedRegion = r.value"
            >
              <span class="region-flag">{{ r.flag }}</span>
              <span class="region-name">{{ r.label }}</span>
              <span class="region-code">{{ r.value }}</span>
            </button>
          </div>
        </section>

        <template v-if="selectedRegion">
          <!-- 조회 상태 바 -->
          <div class="status-bar" :class="isFetching ? 'scanning' : 'done'">
            <span class="status-dot"></span>
            <span v-if="isFetching">리소스 스캔 중 — {{ selectedRegion }}</span>
            <span v-else>스캔 완료 — {{ selectedRegion }} · {{ completedCount }} / {{ totalCount }} 서비스</span>
            <div class="progress-track" v-if="isFetching">
              <div class="progress-fill" :style="{ width: progressPct + '%' }"></div>
            </div>
          </div>

          <!-- 서비스 그리드 -->
          <section class="services-section">
            <div class="cat-panel" v-for="cat in serviceCategories" :key="cat.label">
              <div class="cat-header">
                <span class="cat-icon">{{ cat.icon }}</span>
                <span class="cat-label">{{ cat.label }}</span>
                <span class="cat-total">
                  {{ cat.services.filter(s => s.count !== null).length }} / {{ cat.services.length }}
                </span>
              </div>
              <div class="svc-rows">
                <div class="svc-row" v-for="svc in cat.services" :key="svc.key + svc.label">
                  <span class="svc-label">{{ svc.label }}</span>
                  <span v-if="svc.loading" class="badge badge--scan">
                    <span class="pulse"></span> 스캔 중
                  </span>
                  <span v-else-if="svc.error" class="badge badge--err">
                    실패
                  </span>
                  <span v-else-if="svc.count !== null" class="badge badge--ok">
                    <svg width="10" height="10" viewBox="0 0 10 10"><polyline points="1.5,5.5 4,8 8.5,2" stroke="currentColor" stroke-width="1.8" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg>
                    {{ svc.count.toLocaleString() }}개
                  </span>
                  <span v-else class="badge badge--na">—</span>
                </div>
              </div>
            </div>
          </section>

          <!-- 엑셀 다운로드 -->
          <section class="export-section">
            <ExcelDownloadButton
              :tenant-id="tenantId"
              :client-id="clientId"
              :client-secret="clientSecret"
              :subscription-id="subscriptionId"
              :region="selectedRegion"
            />
          </section>
        </template>

        <div v-else class="region-hint">
          <span>↑ 조회할 리전을 선택하세요</span>
        </div>
      </main>

      <footer class="footer">
        <span>© 2026 Azure Inventory · Powered by Vue 3 & FastAPI</span>
      </footer>
    </div>
  </div>
  <div class="toast-stack" v-if="notifications.length">
    <div class="toast" v-for="n in notifications" :key="n.id">
      <div class="toast-header">
        <span class="toast-title">{{ n.title }}</span>
        <span class="toast-time">{{ n.time }}</span>
      </div>
      <div class="toast-body">{{ n.message }}</div>
      <button class="toast-close" @click="dismissNotification(n.id)">닫기</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue';
import LoginButton from './components/LoginButton.vue';
import ExcelDownloadButton from './components/ExcelDownloadButton.vue';
import { API_BASE_URL } from './config.js';

const isLoggedIn  = ref(false);
const userName    = ref('');
// ── State ─────────────────────────────────────────────────────────────────────
const tenantId    = ref('');
const clientId    = ref('');
const clientSecret= ref('');
const subscriptionId = ref('');
const selectedRegion = ref('');
const isFetching  = ref(false);
const counts      = ref({});
const loadingKeys = ref(new Set());
const errors      = ref({});
const notifications = ref([]);
let notifSeq = 0;
const subscriptions = ref([]);
const subsLoading = ref(false);
const subsError = ref('');

// ── 세션 복원 (페이지 로드 시) ─────────────────────────────────────────────
onMounted(() => {
  const saved = localStorage.getItem('azure_inventory_session');
  if (saved) {
    try {
      const data = JSON.parse(saved);
      
      // 세션 만료 확인 (10분 = 600000ms)
      const now = Date.now();
      const savedTime = data.timestamp || 0;
      const TEN_MINUTES = 10 * 60 * 1000;
      
      if (now - savedTime > TEN_MINUTES) {
        // 세션 만료
        console.log('세션이 만료되었습니다. (10분 초과)');
        clearSession();
        return;
      }
      
      // 세션 복원
      if (data.tenantId) tenantId.value = data.tenantId;
      if (data.clientId) clientId.value = data.clientId;
      if (data.clientSecret) clientSecret.value = data.clientSecret;
      if (data.subscriptionId) subscriptionId.value = data.subscriptionId;
      if (data.region) selectedRegion.value = data.region;
      
      // 모든 정보가 있으면 자동 로그인
      if (data.tenantId && data.clientId && data.clientSecret && data.subscriptionId) {
        isLoggedIn.value = true;
        userName.value = '서비스 프린시플';
      }
    } catch (e) {
      console.error('세션 복원 실패:', e);
      clearSession();
    }
  }
});

// ── 세션 저장 (로그인 시) ──────────────────────────────────────────────────
function saveSession() {
  const data = {
    tenantId: tenantId.value,
    clientId: clientId.value,
    clientSecret: clientSecret.value,
    subscriptionId: subscriptionId.value,
    region: selectedRegion.value,
    timestamp: Date.now(), // 현재 시간 저장
  };
  localStorage.setItem('azure_inventory_session', JSON.stringify(data));
}

// ── 세션 삭제 (로그아웃 시) ────────────────────────────────────────────────
function clearSession() {
  localStorage.removeItem('azure_inventory_session');
}
const regionOptions = [
  { value: 'koreacentral',  label: 'Korea Central',   flag: '🇰🇷' },
  { value: 'koreasouth',    label: 'Korea South',      flag: '🇰🇷' },
  { value: 'eastasia',      label: 'East Asia',        flag: '🇭🇰' },
  { value: 'southeastasia', label: 'Southeast Asia',   flag: '🇸🇬' },
];

const totalCount     = 21;
const completedCount = computed(() => totalCount - loadingKeys.value.size);
const progressPct    = computed(() => Math.round((completedCount.value / totalCount) * 100));

function onLogin(account) {
  isLoggedIn.value = true;
  userName.value = account?.name || account?.username || '서비스 프린시플';
  saveSession(); // 세션 저장
}
function onLogout()       { resetAll(); }
function onLogoutClick()  { resetAll(); }
function resetAll() {
  isLoggedIn.value   = false;
  userName.value     = '';
  selectedRegion.value = '';
  counts.value       = {};
  loadingKeys.value  = new Set();
  errors.value       = {};
  notifications.value = [];
  subscriptions.value = [];
  subsError.value = '';
  subsLoading.value = false;
  clearSession(); // 세션 삭제
}

function buildBody() {
  return JSON.stringify({
    tenant_id: tenantId.value, client_id: clientId.value,
    client_secret: clientSecret.value, subscription_id: subscriptionId.value,
    region: selectedRegion.value,
  });
}

function buildAuthBody() {
  return JSON.stringify({
    tenant_id: tenantId.value, client_id: clientId.value,
    client_secret: clientSecret.value,
  });
}

function pushNotification(title, message) {
  notifications.value = [
    { id: ++notifSeq, title, message, time: new Date().toLocaleTimeString() },
    ...notifications.value,
  ].slice(0, 5);
}

async function fetchOne(key, url, parser) {
  try {
    const res  = await fetch(`${API_BASE_URL}${url}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: buildBody() });
    if (!res.ok) {
      let detail = '요청 실패';
      try {
        const err = await res.json();
        if (err?.detail) detail = err.detail;
      } catch { /* ignore */ }
      errors.value = { ...errors.value, [key]: detail };
      pushNotification(`${key} 실패`, detail);
      return;
    }
    const data = await res.json();
    counts.value = { ...counts.value, ...parser(data) };
    if (key in errors.value) {
      const nextErrors = { ...errors.value };
      delete nextErrors[key];
      errors.value = nextErrors;
    }
  } catch {
    errors.value = { ...errors.value, [key]: '요청 실패' };
    pushNotification(`${key} 실패`, '요청 실패');
  } finally {
    const next = new Set(loadingKeys.value);
    next.delete(key);
    loadingKeys.value = next;
  }
}

async function fetchAllSummaries() {
  if (!isLoggedIn.value || !selectedRegion.value) { counts.value = {}; loadingKeys.value = new Set(); return; }
  if (!tenantId.value || !clientId.value || !clientSecret.value || !subscriptionId.value) return;
  counts.value = {}; errors.value = {}; isFetching.value = true;

  const tasks = [
    ['vnet_subnet', '/network/summary',      d => ({ vnet: d.vnet_count, subnet: d.subnet_count })],
    ['nsg',         '/nsg/summary',           d => ({ nsg: d.nsg_count })],
    ['route_table', '/route-table/summary',   d => ({ route_table: d.route_table_count })],
    ['public_ip',   '/public-ip/summary',     d => ({ public_ip: d.public_ip_count })],
    ['lb',          '/load-balancer/summary', d => ({ lb: d.load_balancer_count })],
    ['agw',         '/app-gateway/summary',   d => ({ agw: d.app_gateway_count })],
    ['vwan',        '/virtual-wan/summary',   d => ({ vwan: d.virtual_wan_count })],
    ['vhub',        '/virtual-hub/summary',   d => ({ vhub: d.virtual_hub_count })],
    ['vpngw',       '/vpn-gateway/summary',   d => ({ vpngw: d.vpn_gateway_count })],
    ['er',          '/express-route/summary', d => ({ er: d.express_route_count })],
    ['vm',          '/vm/summary',            d => ({ vm: d.vm_count })],
    ['cae',         '/cae/summary',           d => ({ cae: d.cae_count })],
    ['aca',         '/aca/summary',           d => ({ aca: d.aca_count })],
    ['acr',         '/acr/summary',           d => ({ acr: d.acr_count })],
    ['mongodb',     '/mongodb/summary',       d => ({ mongodb: d.mongodb_count })],
    ['postgresql',  '/postgresql/summary',    d => ({ postgresql: d.postgresql_count })],
    ['redis',       '/redis/summary',         d => ({ redis: d.redis_count })],
    ['aks',         '/aks/summary',           d => ({ aks: d.aks_count })],
    ['ai_search',   '/ai-search/summary',     d => ({ ai_search: d.ai_search_count })],
    ['aoai',        '/aoai/summary',          d => ({ aoai: d.aoai_count })],
    ['ai_foundry',  '/ai-foundry/summary',    d => ({ 
      foundry: d.foundry_count, 
      speech: d.speech_count, 
      form_recognizer: d.form_recognizer_count 
    })],
  ];
  loadingKeys.value = new Set(tasks.map(t => t[0]));
  await Promise.allSettled(tasks.map(([k, u, p]) => fetchOne(k, u, p)));
  isFetching.value = false;
}

async function fetchSubscriptions() {
  subsError.value = '';
  subscriptions.value = [];
  if (!tenantId.value || !clientId.value || !clientSecret.value) {
    subsError.value = 'Tenant ID, Client ID, Client Secret를 먼저 입력해주세요.';
    return;
  }
  subsLoading.value = true;
  try {
    const res = await fetch(`${API_BASE_URL}/subscriptions/list`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: buildAuthBody(),
    });
    if (!res.ok) {
      let detail = '구독 조회 실패';
      try {
        const err = await res.json();
        if (err?.detail) detail = err.detail;
      } catch { /* ignore */ }
      subsError.value = detail;
      pushNotification('구독 조회 실패', detail);
      return;
    }
    const data = await res.json();
    subscriptions.value = data.subscriptions || [];
    if (subscriptions.value.length === 1) {
      subscriptionId.value = subscriptions.value[0].subscription_id;
    }
  } catch {
    subsError.value = '구독 조회 실패';
    pushNotification('구독 조회 실패', '구독 조회 실패');
  } finally {
    subsLoading.value = false;
  }
}

watch([isLoggedIn, selectedRegion], fetchAllSummaries);

// ── region 변경 시 세션 저장 ───────────────────────────────────────────────
watch(selectedRegion, () => {
  if (isLoggedIn.value) {
    saveSession();
  }
});

function s(lk, label, ck) {
  return {
    key: lk,
    label,
    count: ck in counts.value ? counts.value[ck] : null,
    loading: loadingKeys.value.has(lk),
    error: lk in errors.value ? errors.value[lk] : null,
  };
}

function dismissNotification(id) {
  notifications.value = notifications.value.filter(n => n.id !== id);
}

const serviceCategories = computed(() => [
  { label: '네트워킹', icon: '🌐', services: [
    s('vnet_subnet','VNet','vnet'), s('vnet_subnet','Subnet','subnet'),
    s('nsg','NSG','nsg'), s('route_table','Route Table','route_table'),
    s('public_ip','Public IP','public_ip'), s('lb','Load Balancer','lb'),
    s('agw','App Gateway','agw'), s('vwan','Virtual WAN','vwan'),
    s('vhub','Virtual Hub','vhub'), s('vpngw','VPN Gateway','vpngw'),
    s('er','Express Route','er'),
  ]},
  { label: '컴퓨트', icon: '💻', services: [s('vm','VM','vm')] },
  { label: '컨테이너', icon: '📦', services: [
    s('cae','CAE','cae'), s('aca','ACA','aca'), s('acr','ACR','acr'),
    s('aks','AKS','aks'),
  ]},
  { label: '데이터베이스', icon: '🗄️', services: [
    s('mongodb','Cosmos DB (Mongo)','mongodb'), s('postgresql','PostgreSQL','postgresql'),
    s('redis','Redis Cache','redis'),
  ]},
  { label: 'AI / 분석', icon: '🤖', services: [
    s('ai_search','AI Search','ai_search'),
    s('aoai','Azure OpenAI','aoai'),
    s('ai_foundry','Foundry','foundry'),
    s('ai_foundry','Speech Services','speech'),
    s('ai_foundry','Form Recognizer','form_recognizer'),
  ]},
]);
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans+KR:wght@300;400;500;600&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

/* ── 기본 레이아웃 ── */
.app {
  min-height: 100vh;
  background: #0a0e1a;
  color: #e2e8f0;
  font-family: 'IBM Plex Sans KR', sans-serif;
  position: relative;
  overflow-x: hidden;
}

.bg-grid {
  position: fixed; inset: 0; pointer-events: none; z-index: 0;
  background-image:
    linear-gradient(rgba(99,179,237,0.04) 1px, transparent 1px),
    linear-gradient(90deg, rgba(99,179,237,0.04) 1px, transparent 1px);
  background-size: 40px 40px;
}

.layout {
  position: relative; z-index: 1;
  min-height: 100vh;
  display: flex; flex-direction: column;
  max-width: 1100px; margin: 0 auto;
  padding: 0 24px;
}

/* ── 탑바 ── */
.topbar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 16px 0;
  border-bottom: 1px solid rgba(99,179,237,0.12);
}
.topbar-brand { display: flex; align-items: center; gap: 10px; }
.brand-icon { font-size: 1.4rem; color: #63b3ed; }
.brand-name { font-family: 'IBM Plex Mono', monospace; font-size: 1rem; font-weight: 500; letter-spacing: 0.05em; color: #e2e8f0; }
.topbar-right { display: flex; align-items: center; gap: 12px; }
.user-chip {
  display: flex; align-items: center; gap: 6px;
  background: rgba(99,179,237,0.1); border: 1px solid rgba(99,179,237,0.2);
  border-radius: 999px; padding: 4px 12px; font-size: 0.82rem; color: #93c5fd;
}
.user-dot { width: 6px; height: 6px; border-radius: 50%; background: #4ade80; box-shadow: 0 0 6px #4ade80; }
.btn-logout {
  background: transparent; border: 1px solid rgba(248,113,113,0.3);
  color: #f87171; border-radius: 6px; padding: 4px 12px;
  font-size: 0.82rem; cursor: pointer; transition: all 0.2s;
}
.btn-logout:hover { background: rgba(248,113,113,0.1); border-color: #f87171; }

/* ── 로그인 ── */
.login-pane {
  flex: 1; display: flex; align-items: center; justify-content: center; padding: 48px 0;
}
.login-card {
  width: 100%; max-width: 560px;
  background: rgba(15,23,42,0.8);
  border: 1px solid rgba(99,179,237,0.15);
  border-radius: 16px; padding: 40px;
  backdrop-filter: blur(12px);
  box-shadow: 0 0 60px rgba(99,179,237,0.06);
}
.login-header { margin-bottom: 28px; }
.login-header h1 {
  font-size: 1.6rem; font-weight: 600; color: #f1f5f9;
  margin-bottom: 6px;
}
.login-header p { color: #64748b; font-size: 0.9rem; }

.form-grid { display: flex; flex-direction: column; gap: 14px; margin-bottom: 24px; }
.form-field label {
  display: block; font-size: 0.78rem; font-weight: 500;
  color: #94a3b8; margin-bottom: 6px; letter-spacing: 0.04em; text-transform: uppercase;
}
.label-sub { font-weight: 400; color: #475569; text-transform: none; letter-spacing: 0; }
.form-field input {
  width: 100%; background: rgba(30,41,59,0.8);
  border: 1px solid rgba(99,179,237,0.15); border-radius: 8px;
  padding: 10px 14px; font-size: 0.9rem; color: #e2e8f0;
  font-family: 'IBM Plex Mono', monospace;
  transition: border-color 0.2s, box-shadow 0.2s;
  outline: none;
}
.form-field input:focus {
  border-color: rgba(99,179,237,0.5);
  box-shadow: 0 0 0 3px rgba(99,179,237,0.08);
}
.form-field input::placeholder { color: #334155; }

.sub-actions {
  display: flex; align-items: center; gap: 10px; margin-top: 10px;
}
.btn-sub {
  background: rgba(30,41,59,0.8);
  border: 1px solid rgba(99,179,237,0.25);
  color: #93c5fd;
  border-radius: 8px;
  padding: 6px 12px;
  font-size: 0.82rem;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-sub:disabled {
  opacity: 0.6;
  cursor: default;
}
.btn-sub:hover:not(:disabled) {
  border-color: rgba(99,179,237,0.5);
  background: rgba(99,179,237,0.1);
}
.sub-hint {
  font-size: 0.75rem;
  color: #64748b;
}
.sub-select {
  margin-top: 8px;
}
.sub-select select {
  width: 100%;
  background: rgba(30,41,59,0.8);
  border: 1px solid rgba(99,179,237,0.15);
  border-radius: 8px;
  padding: 8px 12px;
  font-size: 0.85rem;
  color: #e2e8f0;
  font-family: 'IBM Plex Mono', monospace;
}
.form-error {
  margin-top: 8px;
  color: #fca5a5;
  font-size: 0.78rem;
}

/* ── 대시보드 ── */
.dashboard { flex: 1; padding: 28px 0 40px; display: flex; flex-direction: column; gap: 24px; }

/* 리전 선택 */
.section-label {
  display: flex; align-items: center; gap: 8px;
  font-family: 'IBM Plex Mono', monospace; font-size: 0.75rem;
  color: #64748b; letter-spacing: 0.08em; text-transform: uppercase;
  margin-bottom: 12px;
}
.section-dot { width: 5px; height: 5px; border-radius: 50%; background: #63b3ed; }

.region-cards { display: flex; gap: 10px; flex-wrap: wrap; }
.region-card {
  display: flex; flex-direction: column; align-items: flex-start;
  background: rgba(15,23,42,0.6); border: 1px solid rgba(99,179,237,0.12);
  border-radius: 10px; padding: 12px 18px; cursor: pointer;
  transition: all 0.2s; min-width: 150px; text-align: left;
}
.region-card:hover { border-color: rgba(99,179,237,0.35); background: rgba(99,179,237,0.05); }
.region-card.active {
  border-color: #63b3ed; background: rgba(99,179,237,0.1);
  box-shadow: 0 0 20px rgba(99,179,237,0.12);
}
.region-flag { font-size: 1.2rem; margin-bottom: 4px; }
.region-name { font-size: 0.85rem; font-weight: 500; color: #cbd5e1; }
.region-code { font-family: 'IBM Plex Mono', monospace; font-size: 0.72rem; color: #475569; margin-top: 2px; }
.region-card.active .region-name { color: #93c5fd; }
.region-card.active .region-code { color: #63b3ed; }

/* 상태 바 */
.status-bar {
  display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
  padding: 10px 16px; border-radius: 8px; font-size: 0.83rem;
  border: 1px solid;
}
.status-bar.scanning {
  background: rgba(99,179,237,0.06); border-color: rgba(99,179,237,0.2); color: #93c5fd;
}
.status-bar.done {
  background: rgba(74,222,128,0.05); border-color: rgba(74,222,128,0.15); color: #86efac;
}
.status-dot {
  width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0;
}
.scanning .status-dot { background: #63b3ed; box-shadow: 0 0 8px #63b3ed; animation: blink 1s infinite; }
.done .status-dot     { background: #4ade80; box-shadow: 0 0 8px #4ade80; }
.progress-track {
  flex: 1; min-width: 100px; height: 3px;
  background: rgba(99,179,237,0.15); border-radius: 999px; overflow: hidden;
}
.progress-fill {
  height: 100%; background: linear-gradient(90deg, #63b3ed, #a78bfa);
  border-radius: 999px; transition: width 0.4s ease;
}
@keyframes blink { 0%,100% { opacity:1 } 50% { opacity:0.3 } }

/* 서비스 그리드 */
.services-section {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 12px;
}
.cat-panel {
  background: rgba(15,23,42,0.7); border: 1px solid rgba(99,179,237,0.1);
  border-radius: 12px; overflow: hidden;
  backdrop-filter: blur(8px);
}
.cat-header {
  display: flex; align-items: center; gap: 8px;
  padding: 10px 14px;
  background: rgba(99,179,237,0.05);
  border-bottom: 1px solid rgba(99,179,237,0.08);
}
.cat-icon { font-size: 0.95rem; }
.cat-label { font-size: 0.78rem; font-weight: 600; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.06em; flex: 1; }
.cat-total { font-family: 'IBM Plex Mono', monospace; font-size: 0.72rem; color: #475569; }

.svc-rows { padding: 4px 0; }
.svc-row {
  display: flex; align-items: center; justify-content: space-between;
  padding: 7px 14px; border-bottom: 1px solid rgba(99,179,237,0.05);
  transition: background 0.15s;
}
.svc-row:last-child { border-bottom: none; }
.svc-row:hover { background: rgba(99,179,237,0.04); }
.svc-label { font-size: 0.85rem; color: #94a3b8; }

/* 배지 */
.badge {
  display: inline-flex; align-items: center; gap: 4px;
  font-family: 'IBM Plex Mono', monospace; font-size: 0.75rem;
  font-weight: 500; padding: 2px 8px; border-radius: 4px;
}
.badge--ok  { background: rgba(74,222,128,0.1); color: #4ade80; border: 1px solid rgba(74,222,128,0.2); }
.badge--scan{ background: rgba(99,179,237,0.1); color: #63b3ed; border: 1px solid rgba(99,179,237,0.2); }
.badge--err { background: rgba(248,113,113,0.12); color: #f87171; border: 1px solid rgba(248,113,113,0.35); }
.badge--na  { background: rgba(71,85,105,0.2);  color: #475569; border: 1px solid rgba(71,85,105,0.3); }
.pulse {
  width: 5px; height: 5px; border-radius: 50%; background: #63b3ed;
  animation: blink 0.9s infinite;
}

.toast-stack {
  position: fixed;
  right: 20px;
  bottom: 20px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  z-index: 9999;
  max-width: 360px;
}
.toast {
  background: rgba(15,23,42,0.95);
  border: 1px solid rgba(248,113,113,0.35);
  color: #e2e8f0;
  border-radius: 10px;
  padding: 12px 14px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.35);
  backdrop-filter: blur(8px);
}
.toast-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.78rem;
  margin-bottom: 6px;
  color: #fecaca;
}
.toast-title { font-weight: 600; }
.toast-time { color: #94a3b8; font-family: 'IBM Plex Mono', monospace; }
.toast-body {
  font-size: 0.82rem;
  color: #e2e8f0;
  word-break: break-word;
}
.toast-close {
  margin-top: 8px;
  background: transparent;
  border: 1px solid rgba(248,113,113,0.45);
  color: #fca5a5;
  border-radius: 6px;
  padding: 4px 10px;
  font-size: 0.72rem;
  cursor: pointer;
}
.toast-close:hover {
  background: rgba(248,113,113,0.1);
}

/* 힌트 */
.region-hint {
  flex: 1; display: flex; align-items: center; justify-content: center;
  color: #334155; font-size: 0.9rem; padding: 48px 0;
}

/* 푸터 */
.footer {
  padding: 20px 0;
  border-top: 1px solid rgba(99,179,237,0.08);
  text-align: center; font-size: 0.78rem; color: #334155;
}

/* 버튼 전역 리셋 (LoginButton용) */
:deep(button) {
  font-family: 'IBM Plex Sans KR', sans-serif;
}
</style>