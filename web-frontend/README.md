# Podcast Automation Web Frontend

간단한 React + Chakra UI 대시보드로 Automation Service(FastAPI) 데이터를 시각화합니다.

## 사전 요구사항
- Node.js 20 이상
- Automation Service (`uvicorn automation_service.main:app --reload`)가 실행 중이어야 합니다.

## 환경 변수
`.env` 파일을 만들고 API 주소를 지정합니다.
```bash
cp .env.example .env
```

## 실행
```bash
npm install
npm run dev -- --host
```
- 기본 포트는 `5173`이며, 다른 장치에서 접속하려면 `--host` 플래그를 유지하세요.
- 프로덕션 번들: `npm run build`

## 기능
- 채널/플레이리스트/스케줄 목록 및 CRUD 모달 (Automation Service API 연동)
- 작업 큐 패널: Castopod 슬러그/재생목록 UUID를 입력해 큐에 추가·제거하고 “실행” 버튼으로 `manual_trigger` run을 생성
- 큐 모달에서 Castopod 슬러그/UUID 자동 채움 및 “Castopod 자동 업로드” 스위치 제공(기본은 수동 업로드)
- 작업 큐 카드는 단계별 진행률/메시지를 표시하고, `취소` 버튼으로 실행 중인 작업도 중단할 수 있습니다.
- 실행 로그 패널: 상태/메시지 필터, 수동 실행 버튼, 최신 순 정렬
- 다크/라이트 모드 전환 + 30초 자동 새로고침 토글
- Bearer 토큰 저장/로그아웃 UX (현재 API는 인증 없이도 동작)
- Castopod 재생목록 UUID를 모달에서 바로 불러오기 지원(`Castopod DB 조회` 버튼). Automation Service에 Castopod DB 연결 정보가 설정되어 있어야 합니다.

## 향후 확장 아이디어
- 실행 로그 상세 뷰 및 필터링
- 채널/플레이리스트 CRUD용 모달
- WebSocket 기반 실시간 진행 상황 표시
