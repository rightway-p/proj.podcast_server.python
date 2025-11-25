# Work Log

## 2025-10-21 22:38 KST
- Reviewed `podcast_automation_beginner_guide.md` to capture key instructions for future tasks.
- Created `AI/podcast_automation_beginner_checklist.md` with checkbox-based breakdown of the guide.
- Marked checklist progress for sections 1–3 as tasks were completed.
- Generated project folder skeleton under `podcast-server/` (`data/` subdirectories and `traefik/`).
- Authored `podcast-server/compose.yml` containing Traefik, Castopod, MariaDB, and Redis services.
- Populated `podcast-server/.env` with starter configuration values for local deployment.

## 2025-10-21 22:40 KST
- Added 상세 한글 주석 to `podcast-server/compose.yml` 설명 각 서비스/설정 역할.
- Updated `podcast-server/.env` with Korean comments clarifying 환경변수 의미.

## 2025-10-21 22:44 KST
- Created `.gitignore` and `.gitattributes` to establish repository defaults.
- Made initial commit `chore: add repository defaults` containing the housekeeping files.

## 2025-10-21 22:53 KST
- Committed AI documentation assets (`docs: add podcast automation references`).
- Committed Castopod compose stack with Korean comments (`infra: scaffold castopod stack`).

## 2025-10-21 23:02 KST
- Escaped `$` in `MYSQL_ROOT_PASSWORD` within `.env` to satisfy docker compose variable parsing.
- Updated `compose.yml` to drop deprecated `version` field and enforce `linux/amd64` platform for Castopod on Apple Silicon.

## 2025-10-21 23:10 KST
- Replaced MariaDB healthcheck command with `mariadb-admin ping` to match binaries provided in the 11.x image.

## 2025-10-21 23:35 KST
- Sanitized `.env` formatting (removed inline comments) and added required Castopod variables (base URLs, salts, database credentials, MYSQL_* aliases).
- Recreated Castopod service; verified container now stays up with Redis/MariaDB healthy.

## 2025-10-22 23:25 KST
- Updated Traefik service definition to route Castopod through container port 8000 (was 9000).
- Recreated stack; confirmed all services stay healthy (Traefik now proxies http://localhost correctly).

## 2025-10-22 23:37 KST
- Exposed HTTPS port (443) on Traefik, enabled TLS entrypoint, and bound router to proxy network so Traefik forwards traffic to Castopod.

## 2025-10-25 16:42 KST
- Added progress checklist to `AI/podcast_automation_beginner_guide.md` reflecting completed setup stages.

## 2025-10-25 17:20 KST
- Marked Castopod deployment tasks complete in `AI/podcast_automation_beginner_checklist.md` (stack running, admin access, channel + RSS confirmed).

## 2025-11-03 20:45 KST
- Verified `yt-dlp`와 `ffmpeg` 설치 상태 및 버전을 확인해 오디오 변환 준비를 완료했습니다.
- `yt-dlp`로 유튜브 샘플 영상을 `AI/tmp/youtube_test.mp4`로 다운로드했습니다.
- `ffmpeg`를 사용해 mp3(`AI/tmp/youtube_test.mp3`)로 변환해 품질을 검증했습니다.
- `AI/podcast_automation_beginner_checklist.md`의 5번 항목 중 완료된 체크박스를 업데이트했습니다.

## 2025-11-03 21:05 KST
- Castopod 접근 경로와 수동 업로드 절차를 정리한 루트 `README.md`를 신규 작성했습니다.
- Traefik 대시보드 URL(`/dashboard/#/`)과 Castopod 로그인/관리 경로(`cp-auth`, `cp-admin`) 정보를 README에 반영했습니다.
- 사용자 화면에서는 사이드바가 보이지 않는 점을 README에서 주석 처리하여 혼동을 줄였습니다.

## 2025-11-03 21:30 KST
- 에피소드 URL 404 이슈를 재현해 DB 상태를 확인한 결과, 팟캐스트가 `Locked` 상태라 공개 URL이 막혀 있음을 파악했습니다.
- `README.md`에 Access 설정을 Public로 전환해야 한다는 주석을 추가해 향후 혼선을 줄이도록 했습니다.

## 2025-11-03 21:45 KST
- Castopod에서 mp3 수동 업로드 테스트를 완료하고 에피소드를 발행했습니다.
- `AI/podcast_automation_beginner_checklist.md` 5번 항목의 마지막 체크박스를 완료 처리했습니다.

## 2025-11-04 09:20 KST
- Castopod 표지·에피소드 이미지가 깨지는 이슈를 확인한 뒤 `.env`의 `CP_BASE_URL/CP_MEDIA_BASEURL`이 `http://`로 남아 있었다는 원인을 파악했습니다.
- 값을 `https://localhost`로 수정하고 컨테이너 재시작 후 이미지가 정상 노출됨을 검증했습니다.

## 2025-11-04 20:16 KST
- Traefik 서비스에 동적 TLS 구성(`traefik/dynamic/local-certs.yml`)을 추가하고 mkcert 인증서 경로를 마운트했습니다.
- Traefik compose 정의에 파일 프로바이더와 로컬 인증서 볼륨을 연동해 `https://localhost`에서 신뢰된 인증서를 사용하도록 준비했습니다.
- README에 mkcert 설치·생성·재시작 절차를 문서화해 macOS에서 보안 경고 없이 접근할 수 있도록 안내했습니다.

## 2025-11-04 20:37 KST
- `TRUST_STORES=system mkcert ...` 명령으로 Traefik용 `localhost.pem`/`localhost-key.pem`을 생성해 Java 키스토어 경고 없이 인증서를 준비했습니다.
- 생성한 인증서를 Traefik 볼륨에 배치한 뒤 `docker compose up -d traefik --force-recreate`로 리버스 프록시를 재시작해 HTTPS 오류(`ERR_SSL_UNRECOGNIZED_NAME_ALERT`)를 해소했습니다.

## 2025-11-04 20:39 KST
- 자동화 파이프라인 6단계(스케줄러 → 다운로더 → 트랜스코더 → 메타데이터 → 업로더 → 노티파이어)를 정의하고 실행 순서·실패 처리 전략을 정리했습니다.
- `supercronic` 컨테이너에서 일 2회(07:00/19:00 KST) 실행하도록 기본 크론(`PIPELINE_CRON=0 7,19 * * *`)을 선정하고 `.env` 변수화 계획에 반영했습니다.
- `yt-dlp`, `ffmpeg`, Castopod REST API 인증 흐름을 포함한 통합 방식(토큰 기반 업로드, JSON payload 전달)으로 정리해 체크리스트의 6번 항목을 완료 처리했습니다.

## 2025-11-04 20:41 KST
- 상세 설계 문서 `AI/automation_pipeline_plan.md`를 신규 작성해 단계별 모듈, 환경 변수, 폴더 구조, 에러 처리 전략을 시각 다이어그램과 함께 정리했습니다.
- 가이드와 체크리스트에서 새 문서를 직접 참조하도록 링크를 추가해 실제 작업 내용을 빠르게 확인할 수 있게 했습니다.

## 2025-11-04 20:56 KST
- 자동화 관리 방향을 REST API(+SQLite) → TUI → 웹 프런트 순으로 확장하는 3-Phase 로드맵으로 확정하고 관련 TODO를 가이드, 체크리스트, README에 반영했습니다.
- 체크리스트에 백엔드 API 구축, TUI 도구 구현, 웹 UI 검토 등 하위 작업을 세분화해 추적 가능하도록 정리했습니다.

## 2025-11-04 20:59 KST
- README의 Castopod 접속 안내에 로그인(`https://localhost/cp-auth/login`)과 관리자 콘솔(`https://localhost/cp-admin`) URL을 명시하고 표기 정렬을 수정했습니다.

## 2025-11-04 21:09 KST
- `automation-service/` FastAPI 프로젝트를 스캐폴딩하고 SQLite 기반 데이터모델(채널, 플레이리스트, 스케줄, 실행 로그)을 SQLModel로 정의했습니다.
- CRUD 엔드포인트와 `/health` 응답을 제공하는 라우터를 구성하고 Dockerfile, 패키지 메타데이터(pyproject)를 추가했습니다.
- README와 파이프라인 설계 문서에 새 API 사용 방법을 기록하고 체크리스트 6-1 하위 작업 상태를 업데이트했습니다.

## 2025-11-04 21:12 KST
- Automation Service 실행 가이드를 conda 환경(`podcast`) 기준으로 갱신하고 `uvicorn ... --reload` 명령의 의미를 README·서비스 README에 명시했습니다.

## 2025-11-04 21:14 KST
- `AI/technical_notes.md`를 신설해 FastAPI/Uvicorn, SQLite/SQLModel, conda 환경 등 핵심 기술 설명을 모았습니다.
- 가이드·체크리스트·README에서 기술 노트 위치를 안내해 언제든 참고할 수 있도록 연결했습니다.

## 2025-11-04 21:26 KST
- `automation-service/tests/`에 FastAPI 라우트와 CRUD 로직을 검증하는 pytest 스위트를 추가하고 인메모리 SQLite를 공유하는 테스트 픽스처를 구성했습니다.
- conda 환경(`podcast`)에서 `pip install -e automation-service[dev]` 후 `pytest`를 실행해 5개의 테스트가 모두 통과함을 확인했습니다.
- README, 서비스 README, 기술 노트에 테스트 실행 절차를 문서화하고 체크리스트 6-1 항목에 테스트 완료 상태를 반영했습니다.

## 2025-11-04 21:34 KST
- `datetime.utcnow()` 사용 지점을 모두 `datetime.now(UTC)` 기반의 헬퍼로 교체해 경고 없이 타임존 정보를 포함한 타임스탬프를 저장하도록 정비했습니다.
- pytest를 재실행해 5개 테스트가 경고 없이 통과(단, FastAPI의 `on_event` 경고만 유지)함을 확인하고, 기술 노트에 UTC 처리 방식을 기록했습니다.

## 2025-11-04 21:38 KST
- FastAPI의 `@app.on_event` 의존성을 lifespan 컨텍스트(`automation_service.main.lifespan`)로 대체해 시작 시 DB 초기화를 수행하도록 수정했습니다.
- pytest를 다시 실행해 5개 테스트 모두 통과했으며, 기술 노트에 lifespan 전환 내용을 추가했습니다.

## 2025-11-23 15:45 KST
- 사용자 요청에 따라 스케줄 자동 실행 및 선택 다운로드 기능을 명시적으로 추적할 수 있도록 `AI/podcast_automation_beginner_checklist.md`에 6-4 섹션을 추가했습니다.
- 새로운 섹션에는 스케줄 CRUD/API, 백그라운드 스케줄러, 대시보드 UI, 작업 생성 폼 개선, 비교 로그 문서화 등 필요한 작업을 순차적으로 나열했습니다.
- 향후 작업 기록을 위해 본 로그와 README 업데이트 지침을 재확인했습니다.

## 2025-11-23 16:20 KST
- 스케줄 데이터 모델을 요일/시간 기반(`days_of_week`, `run_time`)으로 교체하고 API 스키마·CRUD를 업데이트했습니다. SQLite 기존 테이블에 새 컬럼을 추가하는 마이그레이션 헬퍼도 포함했습니다.
- FastAPI lifespan에 백그라운드 스케줄러를 연결해 1분 간격으로 활성 스케줄을 검사하고, 조건이 맞으면 `pipeline-run`을 자동 호출하도록 했습니다. 트리거 결과는 `last_run_at`, `next_run_at`에 기록됩니다.
- `automation-service/README.md`, 루트 체크리스트, 테스트 코드 등을 새로운 스케줄 입력 방식에 맞게 갱신했습니다.

## 2025-11-24 21:35 KST
- 웹 대시보드에서 상단 “스케줄 추가” 버튼을 제거하고, 각 플레이리스트 카드 내에서 스케줄을 직접 추가할 수 있는 버튼을 추가했습니다. 버튼을 누르면 선택된 플레이리스트 ID가 프리필된 스케줄 모달이 열립니다.
- `ScheduleModal` 컴포넌트를 플레이리스트 단일 선택 전용으로 단순화하고, 요일/시간 입력만 받도록 개선했습니다.
- README에 새로운 스케줄 관리 플로우를 문서화하고 체크리스트 6-4 항목을 갱신했습니다.

## 2025-11-20 23:05 KST
- 사용자 피드백을 바탕으로 “UI에서 최소 입력으로 작업 생성 → 파이프라인 실행 → 진행률 확인” 흐름을 명확히 정의했습니다.
- `AI/automation_pipeline_plan.md`에 9장(2025-11-20 재정리)을 추가해 이상적인 Step-by-step 절차, 필요한 API/UX 기능, 커밋 전략을 문서화했습니다.
- 앞으로 진행할 TODO(작업 생성 모달, quick-create API, targeted pipeline 실행 등)를 표 형태로 정리해 후속 작업 지침을 마련했습니다.
- `pipeline/pipeline_client` 패키지를 추가해 REST API에서 채널/플레이리스트/스케줄을 읽어오는 `AutomationServiceClient`와 `PipelineConfiguration` 모델을 구현했습니다.
- FastAPI 앱을 ASGI transport로 불러오는 pytest 스위트를 작성해 활성/비활성 플레이리스트 분기와 중첩 구조를 검증했습니다.
- README, 파이프라인 설계서, 기술 노트, 체크리스트에 새로운 파이프라인 클라이언트 및 테스트 실행 절차를 반영했습니다.

## 2025-11-04 23:29 KST
- `pipeline/pipeline_runner/main.py`를 추가해 REST API에서 받은 채널/플레이리스트 구성을 기반으로 yt-dlp를 실행하는 `pipeline-run` CLI를 구현했습니다.
- 파이프라인 실행 결과를 Automation Service의 `/runs` 엔드포인트로 기록하도록 `AutomationServiceClient`에 `create_run`/`update_run` 메서드를 추가했습니다.
- `yt-dlp` 의존성을 `pipeline/pyproject.toml`에 등록하고, `README` 및 기술 노트에 실행 방법(`pipeline-run --dry-run`)을 문서화했습니다.

## 2025-11-05 00:10 KST
- Castopod 업로드 자동화에 필요한 OAuth 자격 증명을 준비할 수 있도록 `credentials.template.md`를 추가하고 `.gitignore`에 `credentials.local.md` 예시를 등록했습니다.
- README, pipeline README, 기술 노트에 `pipeline-run --dry-run` 실행 전 설치해야 할 `ffmpeg/yt-dlp` 및 자격 증명 문서를 참고하도록 문구를 보강했습니다.

## 2025-11-05 00:19 KST
- `pipeline-run`이 재생목록 메타데이터를 생성하도록 확장해 `downloads/<slug>/<playlist>/metadata/playlist.json`을 작성하고 썸네일·info JSON 경로를 함께 저장합니다.
- `pipeline_client.AutomationServiceClient`에 `/runs` 상태 기록용 메서드를 추가하고, 실행 중 각 재생목록의 상태를 자동으로 업데이트하도록 조정했습니다.
- README, pipeline README, 기술 노트에 메타데이터 출력 경로와 사전 요구사항(yt-dlp/ffmpeg, 자격증명 문서)을 문서화했습니다.

## 2025-11-05 00:45 KST
- `pipeline/pipeline_runner/artwork.py`를 추가해 플레이리스트·에피소드 썸네일을 정사각형(검은 배경) JPEG으로 변환하고 메타데이터에 `square_cover`·`thumbnail_square` 필드를 기록하도록 확장했습니다.
- Pillow 의존성과 회귀 테스트(`pipeline/tests/test_artwork.py`)를 추가하고 `conda run -n podcast python -m pytest`로 7개 테스트 통과를 확인했습니다.
- 개발 환경 설치 절차를 단순화하기 위해 `pipeline/requirements-dev.txt`를 신설하고 가이드/체크리스트/README에 `python -m pip install -r requirements-dev.txt` 지침을 반영했습니다.

## 2025-11-05 01:20 KST
- `web-frontend/`에 React + Vite + Chakra UI 대시보드 스캐폴딩을 추가해 Automation Service 데이터를 시각화했습니다.
- Bearer Token 입력 기반의 간단한 로그인 폼을 제공해 향후 인증 연계를 준비했고, 채널/플레이리스트/스케줄/최근 실행 정보를 카드 형태로 표시했습니다.
- `.env.example`, 실행 README, 루트 `README.md`, 가이드, 체크리스트에 6-3 실행 방법과 UI 스택 정보를 문서화했습니다.
- FastAPI 앱에 CORS 미들웨어를 추가하고 `AUTOMATION_CORS_ALLOW_ORIGINS` 환경 변수로 허용 오리진을 제어할 수 있도록 하여 웹 프런트엔드에서 API를 호출할 때 발생하던 `Network Error`를 해결했습니다.

## 2025-11-05 01:40 KST
- 루트 README에 자동화 로드맵 요약, 세부 확장 계획, 문서 안내 테이블을 추가해 흩어져 있던 정보를 한 눈에 볼 수 있게 정리했습니다.
- `pipeline/README.md`와 `automation-service/README.md`를 재작성해 설치/실행/향후 과제 섹션을 명확히 하고, 루트 README·가이드와 중복되던 내용을 줄였습니다.
- 가이드/체크리스트에 “자동화 기능 확장 로드맵”과 향후 TODO(채널 마법사, 증분 스케줄러, 통합 관리 UI)를 명시해 다음 단계가 무엇인지 명확히 기록했습니다.
- 웹 대시보드에 채널/플레이리스트/스케줄 생성 모달, 실행 로그 패널(필터 + 수동 실행), 자동 새로고침 토글을 추가해 체크리스트 6-3 잔여 항목을 완료했습니다.

## 2025-11-18 00:00 KST
- Automation Service에 Castopod DB 읽기 엔드포인트 `GET /castopod/podcasts`를 추가하고 pymysql 의존성을 포함했습니다. 환경변수(`AUTOMATION_CASTOPOD_DATABASE_URL` 혹은 HOST/USERNAME/PASSWORD/DB_NAME 조합)로 MariaDB 연결을 받아 cp_podcasts 테이블에서 `id/guid/title`을 반환합니다.
- 웹 대시보드 플레이리스트 모달에 “Castopod DB 조회” 버튼과 드롭다운을 추가해 UUID/제목을 바로 불러와 선택 입력할 수 있게 했습니다. 신규 API 클라이언트 `fetchCastopodPodcasts`와 타입을 추가하고 README에 기능 설명을 반영했습니다.

## 2025-11-19 09:10 KST
- automation-service `config.py`에 `.env` 자동 로드를 추가하고, Castopod DB DSN/개별 변수 예시를 담은 `.env.example`를 작성했습니다. 로컬 `.env`에는 Castopod DSN을 URL 인코딩한 비밀번호로 설정했습니다.
- podcast-server `compose.yml`에서 MariaDB 포트 `3306:3306`을 열어 automation-service가 호스트에서 직접 DB 읽기 가능하도록 수정했습니다.

## 2025-11-20 20:25 KST
- FastAPI가 `sqlite:///./automation_service.db`를 읽기 전용으로 마운트해 500이 발생하는 문제를 피하기 위해, `.env`에 `AUTOMATION_DATABASE_URL=sqlite:///./automation_service_local.db`를 지정하고 uvicorn을 재시작했습니다.
- 새 DB 파일(`automation_service_local.db`)을 생성했으므로, 채널/플레이리스트 데이터를 다시 등록해 사용을 재개하도록 안내했습니다.

## 2025-11-20 21:40 KST
- pipeline-run에 Castopod REST API 업로드 단계를 추가했습니다. `CASTOPOD_API_BASE_URL/USERNAME/PASSWORD/USER_ID` 환경 변수로 인증하고, 각 에피소드 mp3·정사각 썸네일을 업로드한 뒤 즉시 발행합니다. Castopod 컨테이너 `.env`에는 `restapi.enabled=true` 등 REST API 옵션을 추가했습니다.
- Automation Service `Job` 모델에 `should_castopod_upload` 필드를 도입하고 DB 마이그레이션 helper를 추가했습니다. 웹 대시보드 작업 큐 모달에는 “Castopod 자동 업로드” 스위치를 넣어 기본 수동, 필요 시 자동 업로드를 선택할 수 있습니다.
- pipeline-run이 `/jobs/` 큐를 읽어 `queued` 작업을 순차 처리하도록 확장하고, 작업 상태/노트를 자동 업데이트하게 만들었습니다. 스케줄 실행과 동일한 경로를 사용해 다운로드·메타데이터 생성·(옵션)Castopod 업로드가 수행됩니다.

## 2025-11-20 23:10 KST
- 작업 큐 진행률/취소 기능을 추가했습니다. Automation Service `jobs` 테이블에 `progress_total`, `progress_completed`, `current_task`, `progress_message` 필드를 도입하고 `/jobs/{id}` 조회를 제공했습니다. SQLite 자동 마이그레이션을 확장하고 삭제 시 관련 데이터가 함께 제거되도록 관계에 cascade 옵션을 설정했습니다.
- `pipeline-run`이 큐 작업을 처리할 때 단계별 상태를 PATCH하고, 각 에피소드 업로드마다 진행률을 업데이트합니다. 사용자가 웹에서 `취소`를 누르면 상태가 `cancelling`으로 바뀌고 파이프라인이 즉시 중단하며 `cancelled`로 마무리합니다.
- 웹 대시보드 작업 큐 카드에 진행 단계, 퍼센트 Progress Bar, 메시지를 표시하고 취소 버튼을 추가했습니다. Manual run 버튼은 `queued` 상태에서만 활성화되며 진행 상황과 메시지를 표시합니다. README/문서도 새로운 UX와 REST API 설정을 반영했습니다.

## 2025-11-24 13:15 KST
- 웹 대시보드 플레이리스트 카드마다 스케줄 리스트에 수정/삭제 아이콘을 배치해 기존 스케줄을 바로 편집·제거할 수 있도록 했습니다. 모달은 선택된 스케줄 내용을 미리 채워 보여주고 삭제 버튼도 제공합니다.
- `ScheduleModal` 구성요소가 생성/수정 모드를 모두 처리하도록 확장하고 삭제 시 확인 및 로딩 상태를 추가했습니다. API 클라이언트에 `updateSchedule`, `deleteSchedule` 요청 함수를 추가했습니다.
- README와 체크리스트에 “카드 내 스케줄 수정/삭제 UX” 항목을 기록했습니다. 프런트엔드 변경 사항으로 별도 자동 테스트는 실행하지 않았으며, 브라우저에서 수동 검증이 필요합니다.

## 2025-11-24 14:05 KST
- 스케줄러가 조건을 만족하면 해당 플레이리스트용 Job을 자동으로 큐에 추가하고 `pipeline-run`을 호출하도록 `automation_service/scheduler.py`를 확장했습니다. 같은 플레이리스트에 `queued`/`in_progress` Job이 있으면 재사용하여 중복 실행을 막습니다. Job에는 `note="스케줄 자동 실행"`을 남겨 웹에서 식별할 수 있도록 했습니다.
- Job 생성 시 Castopod 슬러그/UUID가 설정돼 있으면 `should_castopod_upload`를 자동 활성화해 완전 자동 업로드 플로우를 보장합니다.
- 웹 대시보드가 새 스케줄 Job을 감지하면 토스트로 “스케줄 실행 시작” 알림을 띄우도록 했습니다. README, Automation Service README, 체크리스트에 “스케줄 → 큐 자동 연동” 내용을 문서화했습니다. 별도의 자동 테스트는 돌리지 않았으므로 실제 동작은 uvicorn 실행 + 스케줄 편집으로 검증해야 합니다.

## 2025-11-24 15:10 KST
- Automation Service에 `queue_runner` 백그라운드 워커를 추가해 파이프라인이 비어 있고 큐에 `queued` Job이 남아 있으면 자동으로 `pipeline-run`을 재실행하도록 했습니다. 새로운 환경 변수 `AUTOMATION_QUEUE_RUNNER_ENABLED` / `_INTERVAL_SECONDS`를 도입하고 lifespan에서 스케줄러와 함께 시작·종료합니다.
- 큐 패널(UI)을 개선해 대기 중 작업 수를 한눈에 확인하고, 완료/실패 작업은 “최근 히스토리” 섹션으로 분리했습니다. API 요청 실패 시 토스트로 오류를 알려주도록 삭제·취소·수동 실행 핸들러에 예외 처리를 추가했습니다.
- README와 Automation Service README, 체크리스트에 큐 러너 존재와 동작 방식을 문서화했습니다. 자동 테스트는 미실행입니다.

## 2025-11-24 15:40 KST
- Dockerfile을 재작성해 repo 루트 컨텍스트에서 automation-service와 pipeline-run을 모두 설치하고 ffmpeg/tini를 포함시켰습니다. 다운로드/DB/로그는 `/data` 볼륨으로 분리되고, `PIPELINE_DOWNLOAD_DIR` 기본값을 `/data/downloads`로 고정했습니다.
- `automation-service/docker-compose.yml`과 `.env.docker`를 추가해 Castopod 스택과 별도로 Automation Service 컨테이너를 띄울 수 있게 했습니다. 호스트 DB 연결은 `host.docker.internal`을 사용하며, 결과물은 `automation-service/data/`에 영속화됩니다.
- 루트 README와 automation-service README에 Docker 실행 절차를 문서화했습니다. `docker compose config`로 구성 검증만 수행했으며 실제 컨테이너 실행은 하지 않았습니다.

## 2025-11-24 15:55 KST
- 다운로드 산출물을 FastAPI에서 `/downloads/`와 `/downloads-browser` 경로로 제공하기 위해 `AUTOMATION_DOWNLOAD_ROOT` 설정을 추가하고 StaticFiles + 간단한 브라우저 HTML 페이지를 구현했습니다.
- 웹 대시보드 큐 패널에 “다운로드 폴더 열기” 버튼을 추가해 `${API_BASE_URL}/downloads-browser`를 새 탭으로 띄우도록 했습니다.
- README/automation-service README에 관련 설명을 보강했습니다. 프런트/백 모두 코드 변경만 적용했으며 추가 테스트는 수행하지 않았습니다.

## 2025-11-25 00:20 KST
- `automation-service/docker-compose.yml`에 web-frontend 서비스를 추가하고, Automation Service(18800) + Nginx 정적 사이트(18080)를 한 번에 올릴 수 있는 스택으로 구성했습니다. 웹 컨테이너는 Node/Vite 빌드 → Nginx 서빙 파이프라인을 사용하고, build arg로 `VITE_API_BASE_URL=http://automation-service:8000`을 주입합니다.
- Docker 사용 시 호스트 포트를 18800/18080으로 조정해 다른 서비스와 충돌하지 않도록 했고, README/automation-service README에 새 포트를 문서화했습니다.
- 작업 큐에 “전체 삭제” 기능을 추가했습니다. FastAPI에 `DELETE /jobs/` 엔드포인트를 만들고, 웹 대시보드 큐 패널에 버튼/토스트를 연결했습니다. 동시에 TypeScript 빌드 오류를 해결하기 위해 `@types/node`를 devDependency에 추가하고 `tsconfig.node.json`을 보강했으며, 중복된 `channel_id` 스프레드 경고를 없앴습니다.
