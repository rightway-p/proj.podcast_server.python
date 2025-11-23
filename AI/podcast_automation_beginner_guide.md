# 🧭 자동 팟캐스트 서버 구축 기초 가이드

이 문서는 **비개발자**가 직접 “유튜브 → 팟캐스트 자동 배포 서버”를 구축할 수 있도록 기초 지식과 과정을 단계별로 정리한 가이드입니다.  
모든 과정은 **Docker(도커)** 환경에서 이루어지며, Apple Podcasts 및 Spotify에 RSS를 자동 배포하는 것을 목표로 합니다.

---


## ✅ 진행 현황
- [x] 1️⃣ 개념 이해하기
- [x] 2️⃣ 도커(Docker)란 무엇인가?
- [x] 3️⃣ 사전 준비 (Docker Desktop 설치·폴더 구조 구성)
- [x] 4️⃣ Castopod 서버 실행 (localhost 접근 확인)
- [ ] 5️⃣ 유튜브 → 오디오 변환 테스트
- [x] 6️⃣ 자동화 구조 설계
- [ ] 7️⃣ 대시보드 구성
- [ ] 8️⃣ 저장소 전략 수립
- [ ] 9️⃣ 백업 및 복원 체계 구축
- [ ] 🔟 진행 로드맵 실습 전체 완료

## 1️⃣ 개념 이해하기

### 🎯 목표
- 유튜브 영상을 자동으로 **오디오(mp3)** 로 변환하고  
  → **Castopod 서버**로 업로드하여  
  → Apple Podcasts / Spotify에 자동 배포한다.

### 🔍 주요 구성요소
| 구성요소 | 역할 | 쉬운 비유 |
|-----------|-------|------------|
| **Castopod** | 팟캐스트 방송국 서버 (RSS 자동 발행) | 라디오 방송국 |
| **Scheduler** | 정해진 시간에 유튜브 새 영상 확인 | 알람시계 |
| **Downloader/Converter** | 영상에서 오디오(mp3) 추출 | 소리 추출기 |
| **Uploader** | Castopod에 새 에피소드 등록 | 배달원 |
| **Dashboard** | 작업 모니터링 및 제어 화면 | 조종석 |
| **Docker** | 모든 프로그램을 한 박스로 묶어 실행 | 통조림 공장 |

---

## 2️⃣ 도커(Docker)란 무엇인가?

도커는 **여러 프로그램을 한 번에 묶어 실행할 수 있는 환경**입니다.  
각각의 기능(예: Castopod, DB, 다운로더)을 **컨테이너(container)** 라는 작은 상자에 넣고,  
이 상자들을 동시에 작동시키는 구조라고 보면 됩니다.

🧱 예를 들어:
- Castopod: 팟캐스트 방송국 상자
- DB: 저장소 상자
- Downloader: 유튜브에서 오디오 추출 상자
- Scheduler: 알람시계 상자
- Dashboard: 관리용 상자

이 모든 상자를 **도커가 자동으로 조립하고 관리**해 줍니다.

---

## 3️⃣ 사전 준비 (기초 세팅)

### ✅ 필수 설치
1. **Docker Desktop 설치**
   - Windows / Mac 지원  
   - https://www.docker.com/products/docker-desktop/

2. **도메인 이름 (선택사항)**
   - 외부에서 접근하려면 필요 (예: pod.mydomain.com)
   - 실험 단계에서는 `localhost` 로 충분

3. **기본 폴더 구조**
```
podcast-server/
 ├─ compose.yml         # 도커 설정파일
 ├─ .env                # 환경 변수
 ├─ data/
 │   ├─ db/             # 데이터베이스 저장
 │   ├─ media/          # 오디오, 이미지 저장
 │   └─ backups/        # 백업 저장소
 └─ traefik/            # SSL 인증서 저장
```

---

## 4️⃣ Castopod 서버 실행

### ⚙️ 절차
1. 준비된 `compose.yml` 파일을 이용해 Castopod, DB, 프록시(SSL) 실행
2. 터미널에서 다음 명령어 입력  
   ```bash
   docker compose up -d
   ```
3. 브라우저에서 접속  
   - 로컬: `https://localhost`  
   - 도메인 사용 시: `https://pod.mydomain.com`
4. 관리자 계정 생성 → 첫 번째 채널(쇼) 만들기

### ✅ 확인할 점
- 관리자 페이지에서 mp3 파일을 수동으로 올려보세요.  
- 자동으로 **RSS 피드 주소**가 만들어집니다.  
- 이 주소를 Apple Podcasts 또는 Spotify에 제출하면 자동 반영됩니다.

---

## 5️⃣ 유튜브 → 오디오 변환 테스트

### 🎞️ 핵심 개념
1. **유튜브 영상 다운로드**
2. **소리만 추출(mp3 변환)**
3. **Castopod에 수동 업로드 (테스트)**

### 🧰 사용 도구
- **yt-dlp**: 유튜브 영상 다운로드 도구
- **ffmpeg**: 오디오 변환 도구

```bash
yt-dlp -x --audio-format mp3 https://youtube.com/watch?v=영상ID
```

변환된 mp3를 Castopod에 업로드해, RSS 반영 여부를 확인합니다.

---

## 6️⃣ 자동화 구조 (스케줄러와 파이프라인)

> 📄 **자세한 설계는 `AI/automation_pipeline_plan.md` 문서를 참고하세요.** 단계별 큐 구조, 환경 변수, 오류 처리 방식까지 정리되어 있습니다.

> ℹ️ **기술 설명은 `AI/technical_notes.md`에 정리되어 있습니다.** FastAPI/Uvicorn, SQLite, conda 환경 등 핵심 개념을 수시로 업데이트합니다.

### 🚧 향후 구현 로드맵
1. **Phase 1 – REST API + SQLite 백엔드**
   - FastAPI 서비스에서 플레이리스트·채널·스케줄 CRUD 제공
   - 파이프라인은 API를 통해 설정을 조회하고 실행 로그(`/runs`)를 기록
   - `pipeline-run --dry-run --download-dir downloads`로 yt-dlp 다운로드 흐름을 즉시 검증 가능 (실행 전 `ffmpeg` 설치 필요)
   - `--dry-run` 옵션을 제거하면 실제 오디오(mp3)가 `downloads/<slug>/<playlist>/` 구조로 저장되고 실행 로그가 `/runs`에 기록됨
2. **Phase 2 – TUI 관리자 도구**
   - `pipeline-tui` 명령으로 `Textual` 기반 UI 실행
   - 채널/플레이리스트/스케줄 CRUD 및 즉시 실행 트리거 수행
   - SSH 환경에서도 플레이리스트 등록/해제·스케줄 설정 가능
3. **Phase 3 – 웹 프런트엔드(선택)**
   - 동일 REST API 위에 React/Next UI 구성해 비개발자 접근성 강화
   - 진행 상황 모니터링, 로그 시각화, 알림 설정 등 확장
   - Castopod 재생목록 UUID를 웹 모달에서 바로 선택: Automation Service에 Castopod DB 접속 정보를 넣으면(`AUTOMATION_CASTOPOD_DATABASE_URL` 등) “Castopod DB 조회” 버튼으로 UUID/제목 목록을 불러와 플레이리스트에 매핑할 수 있음
   - `pipeline-run`에서 Castopod REST API(`CASTOPOD_API_*`)로 자동 업로드·발행이 가능하며, 웹 작업 큐에서는 “Castopod 자동 업로드” 토글로 개별 작업의 업로드 여부를 제어

자동화는 여러 단계를 **자동으로 연결**한 흐름입니다.

### 🔁 처리 순서
1. **스케줄러**: 매일/매주 정해진 시간에 새 영상을 확인  
2. **다운로더**: 영상에서 소리만 추출  
3. **변환기**: mp3 포맷으로 맞춤  
4. **정보추출기**: 제목·설명·썸네일 등 정보 생성  
5. **업로더**: Castopod에 새 에피소드 등록  
6. **Castopod**: RSS 자동 업데이트 → Apple/Spotify 반영

### 🧩 각 단계의 역할
| 이름 | 기능 | 설명 |
|------|------|------|
| **yt-watcher** | 새 영상 감시 | 유튜브 API로 새 영상 탐색 |
| **router** | 채널 자동 분류 | 제목·플레이리스트 규칙 기반 |
| **downloader** | 영상 다운로드 | yt-dlp로 영상 다운로드 |
| **transcoder** | 오디오 변환 | ffmpeg으로 품질 표준화 |
| **metadata-builder** | 설명 분석 | 타임스탬프 → 챕터 변환 |
| **uploader** | Castopod 업로드 | 자동 에피소드 생성 |

### 🖼️ 메타데이터 & 커버 자동화
- `pipeline-run` 실행 시 각 플레이리스트 폴더에는 `metadata/playlist.json`과 함께 정사각형 커버 이미지가 생성됩니다.
  - 채널·플레이리스트용: `metadata/artwork/playlist_cover.jpg`
  - 에피소드용: `metadata/artwork/episodes/<video_id>.jpg`
- 썸네일 원본 비율을 유지한 채 위·아래를 검은색으로 채워 1:1 비율(캐스트포드 표준)에 맞춥니다.
- 메타데이터에는 `channel.square_cover`, `playlist.square_cover`, `episodes[].thumbnail_square` 필드가 추가되어 Castopod 업로드나 대시보드에서 그대로 참조할 수 있습니다.
- 실행 준비 절차
  ```bash
  conda activate podcast
  cd pipeline
  python -m pip install -r requirements-dev.txt
  python -m pytest
  ```
  - Pillow/pytest 등 개발 의존성이 함께 설치되며, `conda run -n podcast python -m pytest` 기준으로 7개의 파이프라인 테스트가 통과하는 것을 확인했습니다.

### 🚀 빠른 실행 순서 (복붙용)
1. **환경 준비 (최초 1회)**
   ```bash
   conda activate podcast
   cd ~/WorkSpace/Dev/proj.podcastserver.python/pipeline
   python -m pip install -r requirements-dev.txt
   ```
2. **Automation Service 구동 (새 터미널)**
   ```bash
   conda activate podcast
   cd ~/WorkSpace/Dev/proj.podcastserver.python/automation-service
   uvicorn automation_service.main:app --reload
   ```
3. **파이프라인 실행**
   - 드라이런(메타데이터만):
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
4. **결과 확인 경로**
  ```
  ~/WorkSpace/Dev/proj.podcastserver.python/pipeline/downloads/<채널>/<플레이리스트>/metadata/playlist.json
  ~/WorkSpace/Dev/proj.podcastserver.python/pipeline/downloads/<채널>/<플레이리스트>/metadata/artwork/playlist_cover.jpg
  ~/WorkSpace/Dev/proj.podcastserver.python/pipeline/downloads/<채널>/<플레이리스트>/metadata/artwork/episodes/<video_id>.jpg
  ```

### 🌐 6-3 웹 프런트엔드 (선택)
- UI 스택: **React + Vite + Chakra UI** (`web-frontend/` 디렉터리)
- 기능 요약
  - Automation Service REST API에서 채널/플레이리스트/스케줄/실행 로그를 불러와 카드 형태로 표시
  - Bearer Token 입력 카드 + 저장/토큰 없이 계속하기, 로그아웃 버튼 제공
- 다크/라이트 모드 전환, 수동/자동 새로고침 토글, 실행 로그 패널(필터 + 수동 실행 버튼)
- 채널/플레이리스트/스케줄 CRUD 모달 + 작업 큐(Queue) 관리 패널 추가 — 실행 전 대기열에서 추가/제거 가능
  - 큐 실행 시 Automation Service의 `/runs/`와 `/jobs/` 엔드포인트에 기록되어 `pipeline-run`이 순차 처리할 준비를 함
- 실행 방법
  ```bash
  cd ~/WorkSpace/Dev/proj.podcastserver.python/web-frontend
  cp .env.example .env   # 필요 시 API 주소 수정
  npm install
  npm run dev -- --host
  ```
  - 기본 API 주소는 `http://127.0.0.1:8000`이며, `Automation Service`가 반드시 실행 중이어야 합니다.
  - API에서 CORS 허용을 위해 `automation-service`의 `.env` 또는 실행 환경에 `AUTOMATION_CORS_ALLOW_ORIGINS`를 설정할 수 있습니다. (기본: `http://localhost:5173`, `http://127.0.0.1:5173`)
  - 브라우저에서 `http://localhost:5173` 접속 후 Bearer Token 입력 없이도 현황을 확인할 수 있습니다.
  - 큐 사용 흐름: (1) 플레이리스트 카드의 **큐에 추가** 버튼 → Castopod 채널/UUID와 작업 유형 선택 → (2) 큐 패널에서 필요 시 제거 → (3) **실행** 버튼으로 파이프라인 수동 실행 트리거

### 🕒 스케줄러(옵저버) 개념
- Castopod에 이미 존재하는 채널/플레이리스트 정보를 Automation Service에 저장한 뒤, 감시할 YouTube 플레이리스트 URL을 매핑합니다.
- 스케줄은 “특정 요일/시간” 단위(주간 반복)로 등록되며, 지정 시간에 유튜브 플레이리스트를 조회 → Castopod 채널과 비교 → 신규 업로드만 다운로드해 Castopod에 추가하는 흐름입니다.
- 스케줄 생성을 원하지 않는 플레이리스트는 큐에만 올려 수동으로 실행할 수 있습니다.

### 🔄 자동화 기능 확장 로드맵
| 영역 | 목표 | 세부 계획 |
|------|------|-----------|
| **채널 생성 마법사** | YouTube 플레이리스트 URL + Castopod 채널 정보를 입력하면 한 번에 다운로드·메타데이터 생성·Castopod 업로드까지 자동 처리 | Automation Service에 마법사 API 추가 → 파이프라인이 즉시 전체 다운로드 실행 → Castopod REST API 모듈로 채널/에피소드 생성 |
| **증분 스케줄러** | 주 단위 요일/시간 스케줄러가 새로운 영상만 감지해 대상 Castopod 채널에 업로드 | 스케줄 모델에 Castopod 채널/UUID 매핑 + 정책 필드 추가 → `pipeline-run` 증분 모드(yt-dlp download archive) → Castopod 업로드 시 중복 체크 |
| **통합 관리 UI** | TUI·웹 UI에서 CRUD, 수동 실행, 실행 로그 상세, 실시간 알림을 제공 | 큐 관리/실행 버튼 → WebSocket/알림 모듈 → 향후 Castopod/YouTube 자격 증명 관리 |

세부 진행 상황은 체크리스트 6-3 하위 TODO와 work log에서 추적합니다.

---

## 7️⃣ 대시보드 구성 (비개발자용 화면)

### 🖥️ 주요 탭 구성
| 탭 이름 | 역할 |
|----------|------|
| **홈** | 채널별 현황, RSS 링크 복사, 저장소 용량 표시 |
| **유튜브 소스 관리** | 감시할 플레이리스트/채널 등록, 스케줄 설정 |
| **라우팅 규칙** | 제목 패턴에 따라 자동 분류 |
| **작업 로그** | 어떤 영상이 변환/업로드됐는지 기록 |
| **저장소 관리** | SSD → NAS → S3 저장소 전환 |
| **백업/복원** | 클릭 한 번으로 백업/되돌리기 |
| **통계** | 다운로드 수, 인기 에피소드 확인 |

---

## 8️⃣ 저장소 이해하기

| 저장소 유형 | 설명 | 특징 |
|--------------|------|------|
| **SSD (기본)** | 내 컴퓨터의 저장공간 | 빠르고 간단 |
| **NAS** | 집/회사 내 네트워크 드라이브 | 대용량, 로컬 접근 |
| **S3 / 클라우드** | 인터넷 저장소 | 안정적, 원격 백업 가능 |

전환 시 도커 설정의 경로만 수정하면 됩니다.

---

## 9️⃣ 백업 및 복원

- **DB 백업**: 하루 1회 자동 저장 (예: 새벽 3시)  
- **오디오 백업**: 주 1회 증분 백업  
- **복원**: 클릭 한 번으로 “어제 상태로 되돌리기”  
- **알림**: 오류 시 이메일/메신저 자동 알림

---

## 🔟 진행 로드맵 (초보자용)

| 주차 | 목표 | 세부 내용 |
|------|------|-----------|
| **1주차** | 환경 구축 | Docker 설치, Castopod 실행 |
| **2주차** | 수동 발행 | mp3 업로드 → RSS 확인 |
| **3주차** | 오디오 변환 | yt-dlp, ffmpeg 실습 |
| **4주차** | 자동화 구성 | 스케줄러, 파이프라인, 대시보드 구상 |

---

## ✅ 요약
- Docker = 여러 프로그램을 안전하게 묶는 상자  
- Castopod = 팟캐스트 방송국  
- 자동화 = 유튜브 → 오디오 → RSS 발행  
- Dashboard = 비개발자용 제어판  
- 백업 = 데이터 안전망

---

## 📚 참고자료
- Castopod 공식 문서: [https://castopod.org/docs/](https://castopod.org/docs/)
- Docker 입문 강의: [https://docker-curriculum.com/](https://docker-curriculum.com/)
- yt-dlp: [https://github.com/yt-dlp/yt-dlp](https://github.com/yt-dlp/yt-dlp)
- ffmpeg: [https://ffmpeg.org/](https://ffmpeg.org/)
