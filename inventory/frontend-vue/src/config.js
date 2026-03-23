// API URL 설정
// 우선순위: 1. window.ENV (런타임) > 2. VITE_API_URL (빌드타임) > 3. 자동 감지
export const API_BASE_URL = 
  (typeof window !== 'undefined' && window.ENV?.API_URL !== '__API_URL__' && window.ENV?.API_URL) ||
  import.meta.env.VITE_API_URL || 
  `${window.location.protocol}//${window.location.hostname}:8000`;

console.log('🔗 API Base URL:', API_BASE_URL);
