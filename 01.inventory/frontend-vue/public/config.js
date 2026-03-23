// Runtime configuration
// 이 파일은 런타임에 Nginx가 주입합니다
window.ENV = window.ENV || {
  API_URL: '__API_URL__'  // 런타임에 치환될 플레이스홀더
};
