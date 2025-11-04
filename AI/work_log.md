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
