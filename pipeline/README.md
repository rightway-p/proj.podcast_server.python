# Pipeline Package

`pipeline/`은 Automation Service API를 소비해 실제 다운로드·메타데이터 생성·Castopod 업로드 준비를 담당하는 실행 도구 모음입니다. CLI(`pipeline-run`), Textual TUI, 회귀 테스트가 한 디렉터리에 있습니다.

## 1. 설치
```bash
conda activate podcast
cd pipeline
python -m pip install -r requirements-dev.txt   # Pillow, pytest 포함
```
- FFmpeg는 시스템에 별도로 설치해야 합니다. (macOS: `brew install ffmpeg`)
- 개발 모드 설치(`pip install -e .`)가 필요하면 위 명령 실행 후 `pip install -e .`를 추가하세요.

## 2. 구성 요소
| 컴포넌트 | 설명 |
|----------|------|
| `pipeline_client/` | Automation Service REST API를 호출해 채널/플레이리스트/스케줄 구성을 받아오는 경량 클라이언트 |
| `pipeline_runner/` | `pipeline-run` CLI, 메타데이터/썸네일 생성, 향후 Castopod 업로드 모듈 위치 |
| `tests/` | 클라이언트·러너 회귀 테스트 (`python -m pytest`) |
| `downloads/` | 실행 산출물이 저장되는 기본 폴더 (git 추적 제외) |

## 3. Textual TUI
```bash
conda activate podcast
pipeline-tui
```
- 기능: 채널/플레이리스트/스케줄 CRUD, 즉시 실행 로그(
`Ctrl+T`
)
- 단축키: `Ctrl+A` 채널 추가, `Ctrl+P` 플레이리스트 추가, `Ctrl+S` 스케줄 추가, `Ctrl+E` 수정, `Ctrl+X` 삭제, `Ctrl+R` 새로고침, `Ctrl+Q` 종료

## 4. Pipeline Runner
```bash
conda activate podcast
pipeline-run --dry-run --download-dir downloads
```
- `--dry-run`을 제거하면 yt-dlp가 실제로 오디오를 내려받아 `downloads/<slug>/<playlist>/`에 저장합니다.
- 각 플레이리스트 폴더에는 `metadata/playlist.json`과 정사각형 커버 이미지(`metadata/artwork/…`)가 생성됩니다.
- 실행 상태는 Automation Service `/runs` API에 기록되고, 큐에 등록된 작업(`jobs`)도 자동으로 소모됩니다.
- 큐 작업(progress)과 취소:
  - `pipeline-run`이 작업을 소비할 때 단계(`downloading`, `metadata`, `uploading`)를 기록하고 총 작업 수 대비 진행률을 업데이트합니다.
  - 웹 대시보드에서 작업 카드가 실시간으로 진행률과 메시지를 표시하며, `취소` 버튼으로 상태를 `cancelling`으로 바꾸면 파이프라인이 즉시 중단합니다.

### 4.1 Castopod REST API 업로드
`pipeline-run`은 플레이리스트에 Castopod Slug/UUID가 매핑돼 있고 아래 환경 변수를 지정하면 에피소드를 자동으로 업로드/발행합니다.

| 환경 변수 | 예시 | 설명 |
|-----------|------|------|
| `CASTOPOD_API_BASE_URL` | `https://localhost/api/rest/v1` | Castopod REST API 엔드포인트 |
| `CASTOPOD_API_USERNAME` | `automation` | Castopod `.env`의 `restapi.basicAuthUsername`와 일치 |
| `CASTOPOD_API_PASSWORD` | `automation` | Castopod `.env`의 `restapi.basicAuthPassword`와 일치 |
| `CASTOPOD_API_USER_ID`  | `1` | 에피소드를 생성/발행할 관리자 사용자 ID |
| `CASTOPOD_API_TIMEZONE` | `Asia/Seoul` | 발행 시 사용할 타임존 (기본 `UTC`) |
| `CASTOPOD_API_VERIFY_SSL` | `false` | 자가 서명 인증서를 사용할 경우 `false` 로 설정 |
| `CASTOPOD_API_EPISODE_TYPE` | `full` | `full/trailer/bonus` 중 하나, 미지정 시 `full` |

Castopod 컨테이너의 `.env`에 아래 값을 추가하고 재시작해야 합니다.
```
restapi.enabled=true
restapi.basicAuth=true
restapi.basicAuthUsername=automation
restapi.basicAuthPassword=automation
```

### 4.2 작업 큐 연동
- 웹 대시보드/TUI에서 큐에 추가한 작업은 `pipeline-run` 실행 시 자동으로 처리되고, 실행 결과에 따라 상태(`queued → in_progress → finished/failed`)가 갱신됩니다.
- 큐 추가 모달에서 “Castopod 자동 업로드” 스위치를 켜면 해당 작업만 업로드를 수행하고, 기본적으로는 다운로드 후 수동 업로드를 전제로 합니다.

## 5. 향후 작업 (자동화 고도화)
1. **채널 생성 마법사 연동**: Automation Service의 새 엔드포인트와 연동해 “이 채널을 지금 즉시 전체 다운로드” 기능 제공
2. **증분 다운로드 모드**: 스케줄 실행 시 신규 업로드만 감지하고 Castopod에 반영
3. **웹/TUI 수동 실행**: 파이프라인 실행을 API/TUI/웹 대시보드에서 원클릭으로 트리거할 수 있도록 확장

세부 설계는 루트 `README.md`와 `AI/podcast_automation_beginner_guide.md`를 참고하세요.
