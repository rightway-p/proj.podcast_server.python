# 기술 노트 (Podcast Automation)

이 문서는 프로젝트에서 사용하는 핵심 기술/명령에 대한 설명을 정리한 참고 자료입니다. 새로운 도구나 명령이 등장하면 여기에 추가합니다.

## FastAPI & Uvicorn
- **FastAPI**: Python 비동기 웹 프레임워크로, REST API를 빠르게 만들 수 있습니다. 타입힌트를 기반으로 자동으로 요청/응답 모델을 검증합니다.
- **Uvicorn**: ASGI(Asynchronous Server Gateway Interface) 서버 구현으로 FastAPI 앱을 실행할 때 주로 사용합니다.
  - `uvicorn automation_service.main:app --reload`
    - `automation_service.main:app`: `automation_service/main.py` 파일 안의 `app` 객체(FastAPI 인스턴스)를 실행 대상으로 지정합니다.
    - `--reload`: 코드가 변경되면 서버를 자동으로 다시 시작합니다. 개발 환경에서만 사용하며, 운영 환경에서는 제거합니다.

## SQLite & SQLModel
- **SQLite**: 파일 기반의 경량 데이터베이스입니다. 별도 서버가 필요 없어 개발 초기 단계에 적합합니다.
- **SQLModel**: Pydantic(데이터 모델 검증)과 SQLAlchemy(ORM)를 결합한 라이브러리입니다. 하나의 모델 클래스로 API 스키마와 데이터베이스 테이블을 동시에 정의할 수 있습니다.
  - 예시: `automation_service/models.py`에서 채널/플레이리스트/스케줄/실행 테이블 정의.
  - `automation_service.database.init_db()` 함수가 애플리케이션 시작 시 테이블을 자동 생성합니다.

## Conda 가상환경
- `conda create -n podcast python=3.12 -y`: `podcast`라는 이름의 Python 3.12 환경을 생성합니다.
- `conda activate podcast`: 방금 만든 가상환경을 활성화합니다.
- 가상환경을 사용하는 이유는 프로젝트별로 라이브러리 버전을 분리해 충돌을 방지하기 위함입니다.

## REST 엔드포인트 요약
- `/channels`: 팟캐스트 채널 CRUD
- `/playlists`: 템플릿에 연결된 YouTube 플레이리스트 관리
- `/schedules`: 각 플레이리스트 실행 주기(cron) 관리
- `/runs`: 파이프라인 실행 로그 기록

## 테스트 실행 흐름
- 프레임워크: `pytest`
- 테스트 위치: `automation-service/tests/`
- 인메모리 SQLite(`StaticPool`)를 사용해 각 테스트가 독립적인 DB 상태로 수행됩니다.
- 실행 명령:
  ```bash
  conda activate podcast
  cd automation-service
  pytest
  ```

## 시간대(UTC) 처리
- 데이터베이스에 저장하는 모든 타임스탬프는 `datetime.now(datetime.UTC)`를 사용해 **타임존 정보가 포함된 UTC** 값으로 기록합니다.
- `automation_service.models.utc_now()` 헬퍼를 통해 기본값을 생성하고, CRUD 업데이트 시에도 같은 방식을 사용합니다.
- 테스트에서도 `datetime.now(UTC)`를 사용하여 경고 없이 동일한 형식을 검증합니다.

## FastAPI Lifespan
- FastAPI 0.110 이상에서는 `@app.on_event` 대신 lifespan 컨텍스트를 권장합니다.
- `automation_service.main.lifespan`에서 데이터베이스 초기화를 수행하며, 앱 생성 시 `FastAPI(..., lifespan=lifespan)`으로 등록합니다.

## Pipeline Client
- 모듈: `pipeline_client.client`
- 주요 클래스: `AutomationServiceClient` (REST 호출), `PipelineConfiguration`
- 테스트에서는 `httpx.ASGITransport`를 사용해 FastAPI 앱과 직접 통신하면서 인메모리 SQLite로 상태를 관리합니다.
- TUI 실행: `pipeline-tui` 명령을 사용하고 단축키는 `Ctrl+A`(채널 추가), `Ctrl+P`(플레이리스트 추가), `Ctrl+S`(스케줄 추가), `Ctrl+E`(수정), `Ctrl+X`(삭제), `Ctrl+R`(새로고침), `Ctrl+T`(즉시 실행 로그), `Ctrl+Q`(종료)입니다.
- 파이프라인 실행: `pipeline-run --dry-run`으로 yt-dlp 기반 다운로드를 시뮬레이션할 수 있으며, 옵션을 제거하면 실제로 오디오 파일을 추출합니다. 실행 결과는 `/runs` 엔드포인트에도 기록됩니다.
- 실행 시 각 플레이리스트 폴더에는 `metadata/playlist.json`이 생성되어 에피소드별 제목, 설명, 썸네일, 오디오 파일 위치를 담아 Castopod 업로드 자동화에 활용할 수 있습니다.

## 향후 추가 예정 노트
- TUI(Textual) 구성 요소 및 단축키 설계
- 파이프라인 컨테이너에서 API를 호출하는 흐름
- 배포 환경에서의 Uvicorn/Gunicorn 구성 패턴
