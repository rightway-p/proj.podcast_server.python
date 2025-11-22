# 자동화 파이프라인 설계서

이 문서는 "유튜브 → 오디오 변환 → Castopod 업로드" 전체 자동화 플로우의 구체적인 설계를 담고 있습니다.

## 1. 전체 개요
- 목표: 지정된 유튜브 채널/플레이리스트의 새 영상을 주기적으로 수집해 팟캐스트 에피소드로 자동 발행
- 실행 단위: `supercronic` 기반 스케줄러 컨테이너가 크론 주기로 파이프라인을 호출
- 결과물: Castopod REST API를 통해 신규 에피소드 등록 및 RSS 자동 갱신

```
 Scheduler ─▶ Watcher ─▶ Router ─▶ Downloader ─▶ Transcoder ─▶ Metadata ─▶ Uploader ─▶ Notifier
                   │                               │                   │                         │
                   └───────────────┬───────────────┴───────────────────┴───────────────┬─────────┘
                                   ▼                                               ▼
                          Dead-letter 로그                                  Artifacts (audio, json)
```

## 2. 스케줄러
- 구현: `docker.io/aptible/supercronic` 이미지 사용
- 기본 주기: `0 7,19 * * *` (KST 기준 하루 2회)
- 환경변수: `PIPELINE_CRON` (필요 시 `.env`에서 수정)
- 실행 방식: 크론 이벤트마다 `python /app/pipeline.py run` 실행

### 2.1 관리 API
- FastAPI 기반 `automation-service/` 프로젝트에서 REST API 제공 (`uvicorn automation_service.main:app`)
- 기본 DB: `automation_service.db` (SQLite). 환경 변수 `AUTOMATION_DATABASE_URL`로 덮어쓰기 가능
- 주요 엔드포인트: `/channels`, `/playlists`, `/schedules`, `/runs`
- OpenAPI 문서는 `http://localhost:8000/docs`

### 2.2 파이프라인 클라이언트
- 위치: `pipeline/pipeline_client`
- `AutomationServiceClient`가 REST API에서 채널/플레이리스트/스케줄을 읽어와 `PipelineConfiguration` 모델로 변환합니다.
- 인메모리 SQLite + FastAPI ASGI transport를 이용한 pytest 스위트가 구성되어 API/클라이언트 연동을 검증합니다.

### 2.3 파이프라인 러너
- 위치: `pipeline/pipeline_runner/`
- 엔트리포인트 `pipeline-run`은 `AutomationServiceClient`로 구성 데이터를 받아 `yt-dlp`를 이용해 재생목록을 다운로드하거나 `--dry-run`으로 시뮬레이션합니다.
- 실행 상태는 Automation Service의 `/runs` 엔드포인트에 기록해 TUI/추후 대시보드에서 확인할 수 있습니다.
- 실행에는 `yt-dlp`, `ffmpeg`가 필요하며 기본 저장 경로는 `downloads/`입니다.

## 3. 단계별 모듈 정의

### 3.1 Watcher
- 입력: `sources.yaml`에 정의된 유튜브 채널/플레이리스트 목록
- 작업: YouTube Data API v3 `playlistItems.list` 호출로 신규 영상 검사
- 출력: `{"video_id":..., "title":..., "published_at":...}` JSON 목록
- 실패 처리: API 오류 시 `dead-letter/watcher/{timestamp}.json` 저장

### 3.2 Router
- 목적: 영상이 어느 팟캐스트 채널에 속할지 규칙 기반 결정
- 규칙 정의: `router_rules.yaml` (예: 제목 패턴, 태그, 플레이리스트 ID)
- 출력: `queue/download` 디렉터리에 라우팅된 작업 JSON 배치

### 3.3 Downloader
- 도구: `yt-dlp`
- 명령: `yt-dlp --write-info-json --no-playlist -o "{tmp}/{video_id}.%(ext)s""
- 산출물: 원본 영상 (`.mp4`), 정보 JSON, 썸네일 이미지
- 실패 처리: 다운로드 실패 시 `dead-letter/downloader/{video_id}.json`

### 3.4 Transcoder
- 도구: `ffmpeg`
- 명령: `ffmpeg -i input.mp4 -ac 2 -ar 44100 -b:a 160k output.mp3`
- 추가: loudness normalization(`-filter:a loudnorm`) 옵션 고려
- 출력: `artifacts/audio/{video_id}.mp3`

### 3.5 Metadata Builder
- 입력: yt-dlp info JSON + 추가 규칙 템플릿 (Jinja2)
- 작업: 에피소드 제목, 설명, 챕터, 커버 이미지 생성
- 출력: `artifacts/meta/{video_id}.json` (Castopod API payload)

### 3.6 Uploader
- 인증: Castopod OAuth 클라이언트 (`CP_API_CLIENT_ID`, `CP_API_CLIENT_SECRET`)
- 절차:
  1. `POST /api/token`으로 액세스 토큰 발급
  2. `POST /api/episodes`로 메타데이터 등록
  3. `POST /api/episodes/{id}/media`에 mp3 업로드 (multipart)
- 성공 시: 에피소드 ID 저장, RSS 갱신 여부 로그 기록

### 3.7 Notifier
- 채널: Slack Webhook 또는 이메일 (추후 결정)
- 메시지: 성공/실패 요약, 링크, 실행 시간

## 4. 파일/폴더 구조 제안
```
pipeline/
 ├─ bin/
 │   ├─ watcher.py
 │   ├─ router.py
 │   ├─ downloader.py
 │   ├─ transcoder.py
 │   ├─ metadata.py
 │   └─ uploader.py
 ├─ configs/
 │   ├─ sources.yaml
 │   ├─ router_rules.yaml
 │   └─ templates/
 ├─ queues/
 │   └─ download/
 ├─ artifacts/
 │   ├─ audio/
 │   ├─ meta/
 │   └─ thumbnails/
 └─ dead-letter/
     ├─ watcher/
     ├─ downloader/
     └─ uploader/
```

## 5. 환경 변수 요약
| 변수 | 설명 | 예시 |
|------|------|------|
| `PIPELINE_CRON` | 파이프라인 실행 일정 | `0 7,19 * * *` |
| `YOUTUBE_API_KEY` | YouTube Data API v3 키 | `AIza...` |
| `CP_API_BASE_URL` | Castopod API 베이스 URL | `https://localhost/api` |
| `CP_API_CLIENT_ID` | Castopod OAuth 클라이언트 ID | `client_xxx` |
| `CP_API_CLIENT_SECRET` | Castopod OAuth 비밀키 | `secret_xxx` |
| `PIPELINE_TMP_DIR` | 임시 작업 디렉터리 | `/pipeline/tmp` |
| `NOTIFY_WEBHOOK_URL` | Slack/Discord Webhook | `https://hooks.slack.com/...` |

## 6. 에러 처리 전략
- 각 단계는 공통 로거(`structlog`)로 JSON 로그 출력
- 실패한 작업은 `dead-letter/<stage>/`에 원인 포함 저장
- 재처리 스크립트: `python pipeline.py retry --stage downloader --since 2h`
- 치명적 오류 발생 시 Notifier가 즉시 알림

## 7. 보안 및 권한
- API 자격증명은 `.env`(로컬) 또는 Docker secret으로 관리
- Artifacts 디렉터리는 `.gitignore`에 추가
- 로그에는 액세스 토큰 등 민감정보 마스킹

## 8. 향후 과제
- [ ] `pipeline/` 디렉터리 스캐폴딩 생성
- [ ] supercronic + 파이썬 파이프라인 이미지를 위한 Dockerfile 작성
- [ ] Castopod API 스키마 검증용 테스트 스크립트 준비
- [ ] Notifier 대상(Slack, Email) 결정 및 비밀정보 설정

## 9. 2025-11-20 — 단계별 실행 흐름 재정리
최근 대시보드/Automation Service/`pipeline-run`을 동시에 쓰면서 UX가 복잡해졌기 때문에, 실제로 사용자가 밟아야 하는 단계를 더 명확히 정의한다.

### 9.1 사용자가 하고 싶은 일
1. “작업” 단위로 **YouTube 플레이리스트 + Castopod 채널**을 연결한다.
2. 등록 즉시 큐/스케줄에 반영되어야 하며, **추가 입력 없이** 동일한 데이터로 실행된다.
3. 웹에서 클릭 한 번으로 파이프라인을 실행하고, 진행률/결과를 즉시 확인한다.

### 9.2 이상적인 단일 플로우 (Step by Step)
1. **작업 생성 모달**  
   - 입력: 작업 이름, YouTube playlist URL, Castopod UUID(혹은 slug), 자동 업로드 여부.  
   - 처리:  
     1. 채널이 없으면 slug를 자동 생성해 만든다.  
     2. 플레이리스트를 채널에 연결한다(YouTube playlist id/slug/UUID 저장).  
     3. 즉시 큐에 Job을 하나 등록하고 필요하면 스케줄도 만들거나 비활성 상태로 둔다.  
   - 출력: 대시보드에 새 작업 카드 표시.
2. **작업 실행**  
   - 사용자는 큐 카드에서 “실행” 혹은 상단의 “파이프라인 실행” 버튼을 클릭한다.  
   - Automation Service는 `/pipeline/trigger`로 `pipeline-run`을 실행한다.  
   - 실행 중 상태는 `jobs.progress_*`와 `runs.progress_*`가 주기적으로 PATCH 된다.
3. **진행 확인**  
   - 대시보드 상단 카드: 현재 파이프라인 프로세스 상태(PID, 로그 경로, 시작/종료 시간).  
   - 작업 큐 카드: `progress_completed/total`, `current_task`를 실시간 표시.  
   - 실행 로그 카드: Run 단위의 진행률과 메시지를 퍼센트 바 + 텍스트로 보여 준다.
4. **완료 후 검증**  
   - 성공 시 Run 상태가 `finished`, Job 상태가 `finished`로 전환되고 Castopod에 에피소드가 올라감.  
   - 실패 시 Run 상태 `failed` + 메시지를 표시하고, Job은 `queued`로 되돌리거나 dead-letter에 남긴다.

### 9.3 구현해야 할 세부 작업
| 구분 | 작업 | 영향 범위 |
|------|------|-----------|
| UX | “작업 생성” 모달 추가 (채널+플레이리스트+큐 동시 생성) | web-frontend, automation-service API |
| API | `/jobs/quick-create` 같은 복합 엔드포인트로 채널/플레이리스트 자동 생성 | automation-service |
| 파이프라인 | 특정 Job/Playlist만 실행하도록 `pipeline-run --playlist-id` 옵션 추가 | pipeline_runner |
| UI | 실행 로그/큐 카드에 progress bar + 단계 텍스트 표시 | web-frontend |
| 관제 | `/pipeline/status` WebSocket/SSE 도입 검토 (지금은 폴링) | automation-service, web-frontend |

### 9.4 진행 로그 & 커밋 전략
1. **Plan Commit**: 본 문서와 `AI/work_log.md`에 개요와 TODO를 작성하고 `git commit -m "docs: outline revised automation workflow"`로 스냅샷 생성.  
2. 이후 기능별(예: `feat(api): add job quick-create endpoint`, `feat(web): add pipeline trigger button`)로 작은 커밋을 쌓는다.  
3. 각 커밋은 rollback 포인트이며, 중간에 문제가 생기면 `git revert <commit>`으로 복원 가능.

### 9.5 다음 스텝
1. **문서/로그 업데이트** (바로 지금 단계)  
   - 이 문서 + work_log에 새로운 설계와 해야 할 일을 명시한다.  
   - 커밋: `docs: outline revised automation workflow`.
2. **Job Quick Create API**  
   - FastAPI 라우터에 POST `/jobs/quick-create` 구현: 채널/플레이리스트 생성 후 job 반환.  
   - 커밋: `feat(api): add quick job creation endpoint`.
3. **UI 작업 생성 모달**  
   - 기존 Channel/Playlist 모달 대신 단일 모달에서 필요한 입력만 받고 quick-create 호출.  
   - 커밋: `feat(web): add job creation wizard`.
4. **Pipeline Runner 옵션**  
   - `pipeline-run`에 `--playlist-id` 혹은 `--job-id` 추가, `/pipeline/trigger`에서 특정 대상만 실행 가능.  
   - 커밋: `feat(pipeline): support targeted playlist execution`.
5. **진행률 표시 강화 + 알림**  
   - Job/Run 카드에 퍼센트/단계 뱃지, 실패 시 빨간 배지 표시.  
   - 커밋: `feat(web): improve job/run progress display`.
