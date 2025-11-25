# Automation Service

FastAPI + SQLModel 기반의 REST API로 채널, 플레이리스트, 스케줄, 실행(run) 정보를 관리합니다. 파이프라인, TUI, 웹 프런트엔드가 모두 이 API를 사용합니다.

## 1. 설치/실행
```bash
conda create -n podcast python=3.12 -y
conda activate podcast
cd automation-service
pip install -e .
uvicorn automation_service.main:app --reload
```
- 기본 DB: `automation_service.db` (SQLite). `AUTOMATION_DATABASE_URL`로 변경 가능.
- CORS: React 대시보드 등 다른 오리진에서 접근하려면 `AUTOMATION_CORS_ALLOW_ORIGINS="http://localhost:5173,https://example.com"`처럼 쉼표로 구분해 설정하세요. 기본값은 `http://localhost:5173`, `http://127.0.0.1:5173`.
- UI에서 `pipeline-run`을 트리거하고 싶다면 아래 값을 설정합니다.
  - `AUTOMATION_PIPELINE_COMMAND="pipeline-run"` (기본: `pipeline-run`)
  - `AUTOMATION_PIPELINE_WORKDIR="/Users/you/WorkSpace/Dev/proj.podcastserver.python/pipeline"` (선택)
  - `AUTOMATION_PIPELINE_LOG_PATH="./pipeline-run.log"` (선택, 실행 로그가 append 됩니다)
- Castopod DB 조회용 설정(읽기 전용): `.env` 혹은 환경변수에 아래 중 하나를 채워두면, API로 UUID를 바로 조회할 수 있습니다.
  - 단일 DSN: `AUTOMATION_CASTOPOD_DATABASE_URL="mysql+pymysql://user:pass@host:3306/castopod"`
  - 혹은 개별 값: `AUTOMATION_CASTOPOD_DB_HOST`, `AUTOMATION_CASTOPOD_DB_PORT`(기본 3306), `AUTOMATION_CASTOPOD_DB_USERNAME`, `AUTOMATION_CASTOPOD_DB_PASSWORD`, `AUTOMATION_CASTOPOD_DB_NAME`
- Castopod 연동 준비(터미널 조회 대안): 위 설정이 없으면 직접 SQL을 실행해 UUID를 조회할 수 있습니다.
  ```bash
  cd podcast-server
  docker compose exec mariadb mariadb -ucastouser -p'비밀번호' castopod \
    -e "SELECT id, guid AS uuid, title FROM cp_podcasts;"
  ```
  조회한 Slug/UUID를 Automation Service UI/TUI에서 수동 입력해두면 이후 `pipeline-run` 업로드 단계가 이를 사용하게 됩니다.
- 스케줄 자동 실행을 원하지 않으면 `AUTOMATION_SCHEDULER_ENABLED=false`로 비활성화할 수 있으며, 기본 60초 주기를 `AUTOMATION_SCHEDULER_INTERVAL_SECONDS=120`처럼 늘려서 부하를 줄일 수 있습니다.
- 큐에 `queued` 작업이 남아 있을 때 파이프라인을 자동으로 재기동하려면 기본값(`AUTOMATION_QUEUE_RUNNER_ENABLED=true`)을 유지하세요. 체크 주기는 `AUTOMATION_QUEUE_RUNNER_INTERVAL_SECONDS`(기본 30초)로 조정할 수 있습니다.
- 파이프라인 다운로드 산출물이 저장될 기본 경로는 `AUTOMATION_DOWNLOAD_ROOT`(기본 `downloads`)입니다. FastAPI가 `/downloads/`(개별 파일)과 `/downloads-browser`(간단한 브라우저 UI) 경로를 제공하므로, 브라우저에서 직접 탐색하거나 웹 대시보드의 “다운로드 폴더 열기” 버튼으로 접근할 수 있습니다.

### Docker 배포
1. `automation-service/.env.docker`를 열어 Castopod 주소, DB DSN, ngrok 호스트 등을 프로젝트 환경에 맞게 수정하세요.  
   - 로컬 MariaDB(Castopod)에 접속하려면 `host.docker.internal` 또는 해당 호스트 IP를 사용합니다.  
   - SQLite/다운로드/로그는 컨테이너 내부 `/data` 경로에 저장되며, 호스트의 `automation-service/data/`와 바인딩됩니다.
2. 동일 디렉터리에서 다음 명령을 실행합니다.
   ```bash
   cd automation-service
   docker compose up -d --build
   ```
3. 브라우저에서 `http://127.0.0.1:8800/docs`로 OpenAPI 문서를 확인하거나, Docker 환경에서는 `http://127.0.0.1:18800`(API) / `http://127.0.0.1:18080`(웹 대시보드)을 사용하세요.
4. 중지/삭제는 `docker compose down`으로 처리하며, 영속 데이터는 `automation-service/data/`에 남습니다.

## 2. 엔드포인트
| 경로 | 설명 |
|------|------|
| `GET/POST /channels/` | 채널 CRUD |
| `GET/POST /playlists/` | 플레이리스트 CRUD |
| `GET/POST /schedules/` | 스케줄 CRUD (요일·시간 + 타임존) |
| `GET/POST /runs/` | 파이프라인 실행(run) 기록 |
| `POST /jobs/quick-create` | 채널/플레이리스트가 없으면 자동 생성 후 Job을 큐에 추가 |
| `GET /castopod/podcasts` | Castopod DB에서 podcast UUID/제목을 읽어옴(읽기 전용) |
| `GET /pipeline/status` | `pipeline-run` 서브프로세스 상태 조회 |
| `POST /pipeline/trigger` | 파이프라인 실행 트리거(이미 실행 중이면 409 반환) |
| `GET /health` | 헬스체크 |

### 스케줄 입력 가이드
- `days_of_week`: `["mon","wed","fri"]`처럼 요일 약어 배열(대소문자 무시). 최소 1개 이상 선택해야 합니다.
- `run_time`: 24시간제 `"HH:MM"` 문자열. 예: `"07:00"`, `"19:30"`.
- `timezone`: IANA 타임존 문자열. 기본값 `"Asia/Seoul"`.
- 서버가 기동되면 백그라운드 워커가 1분 간격으로 활성 스케줄을 검사하고, 해당 요일/시간이 되면 자동으로 `pipeline-run`을 실행합니다. 이미 실행 중이면 Skip 로그가 찍힙니다.
- 스케줄이 조건을 만족하면 동일 플레이리스트에 `queued`/`in_progress` Job이 있는지 확인하고, 없다면 Job을 생성해 큐에 추가한 뒤 `pipeline-run`을 호출합니다. 덕분에 스케줄만 등록해도 큐 버튼을 누를 필요 없이 Castopod 업로드까지 이어집니다.
- 파이프라인이 놀고 있고 큐에 미처리 Job이 남아 있다면, 큐 러너가 자동으로 `pipeline-run`을 다시 실행해 순차 처리합니다. 동시에 여러 스케줄이 Job을 추가해도 파이프라인은 한 번에 하나씩 수행됩니다.

향후 계획
1. **채널 생성 마법사**: Castopod 메타데이터 + YouTube 플레이리스트 URL을 받아 파이프라인을 즉시 실행
2. **증분 스케줄 파라미터**: 스케줄에 Castopod 채널 정보를 연결하고 신규 업로드만 트리거
3. **실행 제어 API**: 수동 실행/재실행, 실행 취소, WebSocket 알림 제공

## 3. 테스트
```bash
conda activate podcast
cd automation-service
pytest
```
테스트는 FastAPI 라우터·CRUD 로직을 인메모리 SQLite로 검증합니다.
