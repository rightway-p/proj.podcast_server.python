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

## 2. 엔드포인트
| 경로 | 설명 |
|------|------|
| `GET/POST /channels/` | 채널 CRUD |
| `GET/POST /playlists/` | 플레이리스트 CRUD |
| `GET/POST /schedules/` | 스케줄 CRUD (크론 표현식 + 타임존) |
| `GET/POST /runs/` | 파이프라인 실행(run) 기록 |
| `POST /jobs/quick-create` | 채널/플레이리스트가 없으면 자동 생성 후 Job을 큐에 추가 |
| `GET /castopod/podcasts` | Castopod DB에서 podcast UUID/제목을 읽어옴(읽기 전용) |
| `GET /pipeline/status` | `pipeline-run` 서브프로세스 상태 조회 |
| `POST /pipeline/trigger` | 파이프라인 실행 트리거(이미 실행 중이면 409 반환) |
| `GET /health` | 헬스체크 |

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
