<template>
  <div class="export-panel">
    <!-- 헤더 -->
    <div class="panel-header">
      <div class="panel-title">
        <span class="panel-icon">📤</span>
        <span>인벤토리 내보내기</span>
      </div>
      <div class="header-actions">
        <button class="text-btn" @click="toggleAll">
          {{ isAllSelected ? '전체 해제' : '전체 선택' }}
        </button>
        <span class="sel-count">{{ selected.length }} / {{ allKeys.length }} 선택</span>
      </div>
    </div>

    <!-- 카테고리 체크 그리드 -->
    <div class="cat-grid">
      <div class="cat-group" v-for="cat in categories" :key="cat.label">
        <div class="cat-group-header">
          <label class="cb">
            <input
              type="checkbox"
              :checked="isCatSelected(cat)"
              :indeterminate.prop="isCatIndeterminate(cat)"
              @change="toggleCategory(cat)"
            />
            <span class="cb-box"></span>
          </label>
          <span class="cat-group-name">{{ cat.icon }} {{ cat.label }}</span>
        </div>
        <div class="svc-checks">
          <label class="cb svc-cb" v-for="svc in cat.services" :key="svc.key">
            <input type="checkbox" :value="svc.key" v-model="selected" />
            <span class="cb-box"></span>
            <span class="cb-label">{{ svc.label }}</span>
          </label>
        </div>
      </div>
    </div>

    <!-- 다운로드 버튼 -->
    <div class="panel-footer">
      <div class="export-info" v-if="selected.length > 0">
        <span class="mono">{{ selected.length }}</span>개 시트가 포함된 xlsx 파일
      </div>
      <div class="export-info muted" v-else>항목을 선택하세요</div>
      <button
        class="btn-export"
        :disabled="selected.length === 0 || loading"
        @click="downloadExcel"
      >
        <span v-if="loading" class="btn-inner">
          <span class="spin"></span> 생성 중...
        </span>
        <span v-else class="btn-inner">
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
            <path d="M7 1v8M4 6l3 3 3-3M2 11h10" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          엑셀 다운로드
        </span>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { API_BASE_URL } from '../config.js';

const props = defineProps({
  tenantId:       { type: String, required: true },
  clientId:       { type: String, required: true },
  clientSecret:   { type: String, required: true },
  subscriptionId: { type: String, required: true },
  region:         { type: String, required: true },
});

const loading = ref(false);

const categories = [
  { label: '네트워킹', icon: '🌐', services: [
    { key: 'vnet_subnet',   label: 'VNet / Subnet' },
    { key: 'nsg',           label: 'NSG' },
    { key: 'route_table',   label: 'Route Table' },
    { key: 'public_ip',     label: 'Public IP' },
    { key: 'load_balancer', label: 'Load Balancer' },
    { key: 'app_gateway',   label: 'App Gateway' },
    { key: 'virtual_wan',   label: 'Virtual WAN' },
    { key: 'virtual_hub',   label: 'Virtual Hub' },
    { key: 'vpn_gateway',   label: 'VPN Gateway' },
    { key: 'express_route', label: 'Express Route' },
  ]},
  { label: '컴퓨트', icon: '💻', services: [{ key: 'vm', label: 'VM' }] },
  { label: '컨테이너', icon: '📦', services: [
    { key: 'cae', label: 'CAE' },
    { key: 'aca', label: 'ACA' },
    { key: 'acr', label: 'ACR' },
    { key: 'aks', label: 'AKS' },
  ]},
  { label: '데이터베이스', icon: '🗄️', services: [
    { key: 'mongodb',    label: 'Cosmos DB (MongoDB)' },
    { key: 'postgresql', label: 'PostgreSQL' },
    { key: 'redis',      label: 'Redis Cache' },
  ]},
  { label: 'AI / 분석', icon: '🤖', services: [
    { key: 'ai_search',       label: 'AI Search' },
    { key: 'aoai',            label: 'Azure OpenAI' },
    { key: 'foundry',         label: 'Foundry' },
    { key: 'speech',          label: 'Speech Services' },
    { key: 'form_recognizer', label: 'Form Recognizer' },
  ]},
];

const allKeys = computed(() => categories.flatMap(c => c.services.map(s => s.key)));
const selected = ref([...allKeys.value]);

const isAllSelected   = computed(() => selected.value.length === allKeys.value.length);
const isIndeterminate = computed(() => selected.value.length > 0 && selected.value.length < allKeys.value.length);

function toggleAll() { selected.value = isAllSelected.value ? [] : [...allKeys.value]; }
function isCatSelected(cat) { return cat.services.every(s => selected.value.includes(s.key)); }
function isCatIndeterminate(cat) {
  const keys = cat.services.map(s => s.key);
  const n = keys.filter(k => selected.value.includes(k)).length;
  return n > 0 && n < keys.length;
}
function toggleCategory(cat) {
  const keys = cat.services.map(s => s.key);
  selected.value = isCatSelected(cat)
    ? selected.value.filter(k => !keys.includes(k))
    : [...new Set([...selected.value, ...keys])];
}

async function downloadExcel() {
  if (!props.tenantId || !props.clientId || !props.clientSecret || !props.subscriptionId) {
    alert('인증 정보를 모두 입력해주세요.'); return;
  }
  if (!props.region) { alert('리전을 선택해주세요.'); return; }
  if (!selected.value.length) { alert('항목을 하나 이상 선택해주세요.'); return; }

  loading.value = true;
  try {
    const res = await fetch(`${API_BASE_URL}/export/inventory`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        tenant_id: props.tenantId, client_id: props.clientId,
        client_secret: props.clientSecret, subscription_id: props.subscriptionId,
        region: props.region, services: selected.value,
      }),
    });
    if (!res.ok) throw new Error(await res.text().catch(() => '다운로드 실패'));
    const blob = await res.blob();
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href = url; a.download = `azure_inventory_${props.region}.xlsx`;
    document.body.appendChild(a); a.click(); a.remove();
    URL.revokeObjectURL(url);
  } catch (e) {
    alert('오류: ' + (e.message || e));
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans+KR:wght@300;400;500;600&display=swap');

.export-panel {
  background: rgba(15,23,42,0.8);
  border: 1px solid rgba(99,179,237,0.15);
  border-radius: 14px;
  overflow: hidden;
  backdrop-filter: blur(10px);
  font-family: 'IBM Plex Sans KR', sans-serif;
}

/* 헤더 */
.panel-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 20px;
  background: rgba(99,179,237,0.05);
  border-bottom: 1px solid rgba(99,179,237,0.1);
}
.panel-title {
  display: flex; align-items: center; gap: 8px;
  font-size: 0.88rem; font-weight: 600; color: #cbd5e1;
}
.panel-icon { font-size: 1rem; }
.header-actions { display: flex; align-items: center; gap: 12px; }
.text-btn {
  background: none; border: none; cursor: pointer;
  color: #63b3ed; font-size: 0.78rem;
  font-family: 'IBM Plex Sans KR', sans-serif;
  padding: 2px 0; text-decoration: underline; text-underline-offset: 2px;
}
.text-btn:hover { color: #93c5fd; }
.sel-count {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 0.75rem; color: #475569;
}

/* 카테고리 그리드 */
.cat-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 0;
  border-bottom: 1px solid rgba(99,179,237,0.08);
}
.cat-group {
  padding: 14px 16px;
  border-right: 1px solid rgba(99,179,237,0.06);
  border-bottom: 1px solid rgba(99,179,237,0.06);
}
.cat-group:last-child { border-right: none; }

.cat-group-header {
  display: flex; align-items: center; gap: 8px;
  margin-bottom: 10px; padding-bottom: 8px;
  border-bottom: 1px solid rgba(99,179,237,0.08);
}
.cat-group-name { font-size: 0.78rem; font-weight: 600; color: #64748b; letter-spacing: 0.04em; }

.svc-checks { display: flex; flex-direction: column; gap: 6px; }
.svc-cb { cursor: pointer; }

/* 커스텀 체크박스 */
.cb {
  display: inline-flex; align-items: center; gap: 8px; cursor: pointer;
}
.cb input[type="checkbox"] { position: absolute; opacity: 0; width: 0; height: 0; }
.cb-box {
  width: 14px; height: 14px; border-radius: 3px; flex-shrink: 0;
  border: 1px solid rgba(99,179,237,0.3);
  background: rgba(15,23,42,0.8);
  position: relative; transition: all 0.15s;
}
.cb input:checked + .cb-box {
  background: #2563eb; border-color: #2563eb;
}
.cb input:checked + .cb-box::after {
  content: '';
  position: absolute; top: 1px; left: 3px;
  width: 6px; height: 4px;
  border-left: 1.5px solid #fff; border-bottom: 1.5px solid #fff;
  transform: rotate(-45deg);
}
.cb input:indeterminate + .cb-box {
  background: rgba(37,99,235,0.4); border-color: #2563eb;
}
.cb input:indeterminate + .cb-box::after {
  content: '';
  position: absolute; top: 5px; left: 2px;
  width: 8px; height: 1.5px; background: #fff;
}
.cb-label { font-size: 0.82rem; color: #94a3b8; transition: color 0.15s; }
.svc-cb:hover .cb-label { color: #cbd5e1; }
.svc-cb:hover .cb-box { border-color: rgba(99,179,237,0.6); }

/* 푸터 */
.panel-footer {
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 20px; gap: 16px;
}
.export-info { font-size: 0.82rem; color: #64748b; }
.export-info.muted { color: #334155; }
.mono { font-family: 'IBM Plex Mono', monospace; color: #93c5fd; font-weight: 500; }

.btn-export {
  display: inline-flex; align-items: center;
  background: linear-gradient(135deg, #1d4ed8, #2563eb);
  border: 1px solid rgba(99,179,237,0.3);
  color: #fff; border-radius: 8px;
  padding: 9px 20px; font-size: 0.88rem; font-weight: 500;
  cursor: pointer; font-family: 'IBM Plex Sans KR', sans-serif;
  transition: all 0.2s; white-space: nowrap;
  box-shadow: 0 0 20px rgba(37,99,235,0.25);
}
.btn-export:hover:not(:disabled) {
  background: linear-gradient(135deg, #1e40af, #1d4ed8);
  box-shadow: 0 0 30px rgba(37,99,235,0.4);
  transform: translateY(-1px);
}
.btn-export:disabled { opacity: 0.4; cursor: default; box-shadow: none; transform: none; }
.btn-inner { display: flex; align-items: center; gap: 7px; }

/* 스피너 */
.spin {
  width: 12px; height: 12px; border-radius: 50%;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: #fff;
  animation: spin 0.7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
</style>