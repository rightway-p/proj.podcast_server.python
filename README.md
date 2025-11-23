# Podcast Automation Sandbox

Castopod 기반의 팟캐스트 자동화 실험 환경입니다. Traefik 리버스 프록시, MariaDB, Redis를 포함한 Docker Compose 스택으로 구성되며 로컬에서 빠르게 테스트할 수 있도록 설계되었습니다.

## 선행 요구사항
- Docker Desktop (또는 호환 가능한 Docker 엔진)
- `podcast-server/.env` 파일 내 도메인 및 비밀번호 값 확인
- CLI 파이프라인 실행을 위해서는 `yt-dlp`, `ffmpeg`가 설치되어 있어야 합니다. `pipeline` 패키지를 설치하면 `yt-dlp`는 의존성으로 내려오며, macOS 기준 `brew install ffmpeg`로 FFmpeg를 준비할 수 있습니다.

## 실행 방법
```bash
cd podcast-server
docker compose up -d
```

## Castopod 접속 방법
- Traefik이 `CP_HOST` 환경변수에 정의된 호스트 이름으로 라우팅합니다. 기본값은 `localhost`입니다.
- 로컬 개발 기본값 기준 접속 주소:
  - 공개 웹: `https://localhost`
  - 로그인: `https://localhost/cp-auth/login`
  - 관리자 콘솔: `https://localhost/cp-admin`
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

## 자동화 로드맵 요약
| Phase | 설명 | 핵심 컴포넌트 |
|-------|------|---------------|
| **1. API & 파이프라인** | Automation Service(FastAPI + SQLite)에서 채널/플레이리스트/스케줄을 관리하고 `pipeline-run`이 설정을 읽어 다운로드/메타데이터 생성 | `automation-service`, `pipeline` |
| **2. TUI 관리 도구** | SSH 환경에서도 CRUD·즉시 실행을 처리할 수 있는 Textual 기반 CLI | `pipeline_client.tui` |
| **3. 웹 프런트(6-3)** | React + Chakra UI 대시보드로 현황을 시각화, 추후 CRUD·수동 실행·알림을 추가 예정 | `web-frontend` |

### 앞으로의 자동화 확장 계획
1. **Castopod 채널 생성 마법사**: Automation Service에 채널 메타데이터와 YouTube 플레이리스트 URL을 입력받는 엔드포인트를 추가하고, 파이프라인이 전체 다운로드 후 Castopod API로 채널/에피소드를 자동 생성
2. **증분 스케줄러**: 스케줄 엔티티에 Castopod 채널 매핑을 보관하고, supercronic→pipeline-run 체인에서 신규 업로드만 다운로드하여 해당 채널에 업로드
3. **통합 관리 UI**: TUI/web에서 채널/플레이리스트/스케줄 CRUD, 수동 실행, 실행 로그 상세, 향후 WebSocket 기반 실시간 알림까지 제공

세부 계획과 진행 상황은 `AI/podcast_automation_beginner_guide.md`와 체크리스트를 참고하세요.

## 문서 안내
| 문서 | 설명 |
|------|------|
| `AI/podcast_automation_beginner_guide.md` | 전체 여정을 주차별로 정리한 가이드, 자동화 확장 계획 포함 |
| `AI/podcast_automation_beginner_checklist.md` | 완료/미완료 항목 추적용 체크리스트, 6-3 이후 TODO 포함 |
| `automation-service/README.md` | FastAPI API 서버 개발/실행 가이드 및 CORS 설정 |
| `pipeline/README.md` | 파이프라인 CLI·TUI 사용법, 메타데이터/다운로드 설명 |
| `web-frontend/README.md` | React 대시보드 실행 방법과 향후 확장 아이디어 |

## Automation Service (Phase 1)
- 경로: `automation-service/`
- 로컬 실행 예시:
```bash
cd automation-service
conda create -n podcast python=3.12 -y
conda activate podcast
pip install -e .
uvicorn automation_service.main:app --reload
```
- 위 명령은 uvicorn(ASGI 서버)을 이용해 FastAPI 앱을 개발 모드로 실행합니다.
- `uvicorn automation_service.main:app --reload`는 FastAPI 앱을 개발 모드로 실행하며 코드 변경 시 서버를 자동으로 재시작합니다.
- 기본 DB는 같은 디렉터리의 `automation_service.db`이며 `AUTOMATION_DATABASE_URL`로 변경할 수 있습니다.
- 웹 프런트엔드와 같은 다른 오리진에서 접근하려면 CORS 허용 목록을 지정해야 합니다. 기본값은 `http://localhost:5173`/`http://127.0.0.1:5173`이며, 추가가 필요하면 `AUTOMATION_CORS_ALLOW_ORIGINS="https://example.com,https://foo.bar"`처럼 쉼표로 구분해 설정하세요.
- 추가 기술 설명은 `AI/technical_notes.md`에서 확인할 수 있습니다.
- 테스트 실행:
  ```bash
  conda activate podcast
  cd automation-service
  pytest
  ```
- 파이프라인 클라이언트:
  ```bash
  conda activate podcast
  cd pipeline
  python -m pip install -r requirements-dev.txt
  python -m pytest
  ```
- TUI 실행:
  ```bash
  conda activate podcast
  pipeline-tui
  ```
  (단축키: `Ctrl+A` 채널 추가, `Ctrl+P` 플레이리스트 추가, `Ctrl+S` 스케줄 추가, `Ctrl+E` 수정, `Ctrl+X` 삭제, `Ctrl+R` 새로고침, `Ctrl+T` 즉시 실행 로그, `Ctrl+Q` 종료)
- 파이프라인 실행:
  ```bash
  conda activate podcast
  pipeline-run --dry-run --download-dir downloads
  ```
  - `--dry-run` 옵션을 제거하면 실제 다운로드가 수행됩니다. (FFmpeg가 필요합니다.)
  - 실행 결과는 Automation Service `/runs` 엔드포인트에서도 확인할 수 있습니다.
  - 각 플레이리스트 폴더에는 `metadata/playlist.json`이 생성되어 에피소드별 제목·설명·썸네일·오디오 파일 경로가 정리됩니다.
  - 정사각형 커버 이미지는 `metadata/artwork/playlist_cover.jpg` 및 `metadata/artwork/episodes/<video_id>.jpg`로 저장되며 `playlist.json`의 `square_cover`·`thumbnail_square` 필드와 연결됩니다.

### 웹 프런트엔드 (6-3)
React + Vite + Chakra UI로 만든 경량 대시보드입니다.

```bash
cd web-frontend
cp .env.example .env   # 필요시 API 주소 수정
npm install
npm run dev -- --host
```
- Automation Service가 실행 중이어야 하며 기본 API 주소는 `http://127.0.0.1:8000`입니다.
- 브라우저에서 `http://localhost:5173`로 접속하면 채널/플레이리스트/스케줄 CRUD, 실행 로그 필터/수동 실행, 자동 새로고침을 포함한 현황판을 사용할 수 있습니다.
- 작업 큐: 플레이리스트 카드의 **큐에 추가** 버튼으로 Castopod 채널 정보와 함께 큐에 적재 → 큐 패널에서 제거/실행 → 실행 시 Automation Service `/jobs`와 `/runs`에 기록되므로 `pipeline-run`이 후속 다운로드를 수행합니다.

### 빠른 실행 순서 (복붙용)
1. 환경 준비 *(최초 1회)*
   ```bash
   conda activate podcast
   cd ~/WorkSpace/Dev/proj.podcastserver.python/pipeline
   python -m pip install -r requirements-dev.txt
   ```
2. Automation Service 실행 *(새 터미널)*
   ```bash
   conda activate podcast
   cd ~/WorkSpace/Dev/proj.podcastserver.python/automation-service
   uvicorn automation_service.main:app --reload
   ```
3. 파이프라인 실행
   - 드라이런:
     ```bash
     conda activate podcast
     cd ~/WorkSpace/Dev/proj.podcastserver.python/pipeline
     pipeline-run --dry-run --download-dir downloads
     ```
   - 실제 다운로드:
     ```bash
     conda activate podcast
     cd ~/WorkSpace/Dev/proj.podcastserver.python/pipeline
     pipeline-run --download-dir downloads
     ```
4. 산출물 위치
   ```
   ~/WorkSpace/Dev/proj.podcastserver.python/pipeline/downloads/<채널>/<플레이리스트>/metadata/playlist.json
   ~/WorkSpace/Dev/proj.podcastserver.python/pipeline/downloads/<채널>/<플레이리스트>/metadata/artwork/playlist_cover.jpg
   ~/WorkSpace/Dev/proj.podcastserver.python/pipeline/downloads/<채널>/<플레이리스트>/metadata/artwork/episodes/<video_id>.jpg
   ```
- 주요 REST 엔드포인트: `/channels`, `/playlists`, `/schedules`, `/runs` (OpenAPI: `/docs`).
- Castopod 업로드를 자동화하려면 Castopod 관리자(UI)에서 발급 받은 OAuth Client ID/Secret, 업로드 대상 팟캐스트 UUID 등이 필요합니다. 민감한 값은 프로젝트 루트의 `credentials.example.md`를 참고해 별도의 비공개 파일에 정리하고 `.env` 또는 Docker secrets로 주입하세요.

## 자주 사용하는 명령어 모음
| 작업 | 명령 |
|------|------|
| Automation Service 서버 실행 |`conda activate podcast && cd automation-service && uvicorn automation_service.main:app --host 127.0.0.1 --port 8800 --reload` |
| Automation Service 테스트 | `conda run -n podcast bash -lc 'cd automation-service && pytest'` |
| 파이프라인 러너 실행(드라이런) | `conda activate podcast && cd pipeline && pipeline-run --dry-run --download-dir downloads` |
| 파이프라인 러너 실행(실제 다운로드) | `conda activate podcast && cd pipeline && pipeline-run --download-dir downloads` |
| 파이프라인 Textual TUI | `conda activate podcast && pipeline-tui` |
| 웹 대시보드 개발 서버 | `cd web-frontend && npm install && npm run dev -- --host` |
| Castopod Docker 스택 기동 | `cd podcast-server && docker compose up -d` |
| Castopod 서버 실행 | `conda activate podcast
cd ~/WorkSpace/Dev/proj.podcastserver.python/automation-service
uvicorn automation_service.main:app --host 127.0.0.1 --port 8800 --reload
` |
| Castopod DB에서 UUID 확인 | `docker compose exec mariadb mariadb \
  -u"$CP_DB_USERNAME" -p"$CP_DB_PASSWORD" "$CP_DB_DATABASE" \
  -e "SELECT id, guid AS uuid, title FROM cp_podcasts;"` |
| Castopod DB 접속(패스워드 외부 입력) | `cd podcast-server && docker compose exec mariadb mariadb -ucastouser -p castopod` |

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
