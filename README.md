# Podcast Automation Sandbox

Castopod 기반의 팟캐스트 자동화 실험 환경입니다. Traefik 리버스 프록시, MariaDB, Redis를 포함한 Docker Compose 스택으로 구성되며 로컬에서 빠르게 테스트할 수 있도록 설계되었습니다.

## 선행 요구사항
- Docker Desktop (또는 호환 가능한 Docker 엔진)
- `podcast-server/.env` 파일 내 도메인 및 비밀번호 값 확인

## 실행 방법
```bash
cd podcast-server
docker compose up -d
```

## Castopod 접속 방법
- Traefik이 `CP_HOST` 환경변수에 정의된 호스트 이름으로 라우팅합니다. 기본값은 `localhost`입니다.
- 로컬 개발 기본값 기준 접속 주소:
 - Castopod 웹: `https://localhost`
  - Traefik 대시보드(옵션): `http://localhost:8080/dashboard/#/` (루트 경로는 404를 반환합니다)
- 처음 HTTPS 접속 시 브라우저에서 자가 서명 인증서 경고가 표시될 수 있습니다. 아래 "로컬 HTTPS 인증서 신뢰화" 절차를 완료하면 경고 없이 접속할 수 있습니다.
- 커스텀 도메인을 사용하려면 `.env` 파일의 `CP_HOST`, `CP_BASE_URL`, `CP_MEDIA_BASEURL` 값을 원하는 도메인으로 수정한 뒤 Traefik DNS/인증서 구성을 조정하세요.
 - 새 팟캐스트를 만든 직후에는 기본값이 비공개(`Locked`)입니다. **Dashboard → Podcasts → Settings → Access**에서 공개(Public)로 전환하지 않으면 에피소드 URL이 404로 응답합니다.

## 로컬 HTTPS 인증서 신뢰화
macOS에서 Traefik이 제공하는 `https://localhost` 인증서를 신뢰시키려면 한 번만 아래 절차를 수행하면 됩니다.

1. `brew install mkcert` (필요 시 Firefox는 `brew install nss`도 함께 설치).
2. `mkcert -install`로 로컬 신뢰 루트 인증서를 키체인에 추가합니다.
3. 저장소 루트에서 다음 명령으로 localhost 인증서를 생성합니다.
   ```bash
   mkcert \
     -cert-file podcast-server/traefik/certs/localhost.pem \
     -key-file podcast-server/traefik/certs/localhost-key.pem \
     localhost 127.0.0.1 ::1
   ```
   - 파일은 `.gitignore`에 포함되어 있어 레포지토리에 커밋되지 않습니다.
4. Traefik을 재시작해 새 인증서를 로드합니다.
   ```bash
   cd podcast-server
   docker compose up -d traefik --force-recreate
   ```
5. 브라우저에서 `https://localhost` 접속 후 경고 없이 열리면 완료입니다. 경고가 남아 있다면 브라우저 캐시/인증서 저장소를 비우고 다시 시도하세요.

## 에피소드 수동 업로드 가이드
1. 브라우저에서 `https://localhost/cp-auth/login`으로 이동하거나 공개 페이지 우측 상단의 사용자 아이콘을 눌러 로그인 화면을 연 뒤 관리자 계정으로 로그인합니다.
   - 성공적으로 로그인하면 `https://localhost/cp-admin`(또는 우측 상단 프로필 메뉴 → **Dashboard**)에서 관리 화면을 이용할 수 있습니다.
2. 왼쪽 사이드바에서 **Podcasts** → 원하는 채널 선택(또는 새 채널 생성) → **Episodes**를 클릭합니다.
3. **New episode** 버튼을 누르고 제목, 설명 등 기본 메타데이터를 입력합니다.
4. **Upload media** 단계에서 변환된 mp3 파일(예: `AI/tmp/youtube_test.mp3`)을 업로드합니다.
5. 업로드가 완료되면 발행 시점(즉시/예약)을 설정하고 **Publish**로 마무리합니다.
6. 발행 후 채널 페이지에서 RSS 주소가 정상적으로 갱신됐는지 확인합니다.

## 최초 설정 체크리스트
1. Castopod 초기 마법사에서 관리자 계정 및 첫 채널을 생성합니다.
2. 대시보드에서 RSS 주소를 확인하고 자동화 파이프라인 테스트에 활용합니다.

추가 참고 자료와 작업 기록은 `AI/` 디렉터리에 정리되어 있습니다.
