# 🌙 Loomy Daily

Loomy의 일일 선물 포인트를 갱신하고 8개 온보딩 작업 보상을 받는 단일 Python 스크립트입니다. 다중 계정을 지원합니다.

[简体中文](../README.md) · [English](README.en.md) · [繁體中文](README.zh-Hant.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Português (BR)](README.pt-BR.md)

전체 중국어 문서는 [../README.md](../README.md)에서 확인하세요.

## 주요 기능

- 일일 최초 로그인 API를 호출해 선물 포인트를 날짜 단위로 멱등 갱신합니다.
- 8개 온보딩 작업을 제출하고 최대 10000포인트 진행률을 추적합니다.
- 모든 작업이 정산되면 로컬 완료 스냅샷을 저장합니다.
- `--tasks`, `--claim KEY`, `--refresh`로 조회, 개별 수령, 강제 재확인을 지원합니다.
- SMS 인증 로그인과 줄바꿈 또는 `&`로 구분한 다중 session을 지원합니다.
- PushPlus, Bark, WeCom, DingTalk, Qinglong 알림을 사용할 수 있습니다.

## Qinglong 최소 설정

```bash
python3 -m pip install -r requirements.txt
```

`loomy_daily.py`를 업로드하고 `LOOMY_TOKENS`를 설정한 뒤 작업을 만듭니다.

```text
45 8 * * * task loomy_daily.py
```

온보딩 수령을 끄려면:

```text
45 8 * * * task loomy_daily.py --no-onboarding
```

session 생성:

```bash
python loomy_login.py
python loomy_login.py 13800000000 123456 --note main
python loomy_login.py --verify
```

## GitHub Actions

**Settings → Secrets and variables → Actions**에서 다음 Secrets를 만듭니다.

```text
LOOMY_TOKENS
PUSHPLUS_TOKEN          # 선택
BARK_URL                # 선택
WECOM_WEBHOOK           # 선택
DINGTALK_WEBHOOK        # 선택
DINGTALK_SECRET         # 선택
```

**Actions → Loomy Daily → Run workflow**에서 수동 실행합니다. 기본값은 수동 실행이며, 예약 실행이 필요하면 `.github/workflows/daily.yml`의 `schedule:` 주석을 해제하세요. cron은 UTC 기준입니다.

## 핵심 환경 변수

| 변수 | 용도 |
| :--- | :--- |
| `LOOMY_TOKENS` | 필수. `session` 또는 `note\|session`; 계정은 줄바꿈이나 `&`로 구분 |
| `LOOMY_ONBOARDING` | 기본값 `1`; `0`이면 온보딩 작업 생략 |
| `PUSHPLUS_TOKEN`, `BARK_URL`, `WECOM_WEBHOOK`, `DINGTALK_WEBHOOK`, `DINGTALK_SECRET` | 선택 알림 채널 |
| `QL_URL`, `QL_TOKEN` | 선택 Qinglong 알림 주소와 구버전 패널 토큰 |

## 성공 기준과 개인정보

일일 API가 비즈니스 코드 `000000`을 반환해야 성공입니다. `dailyBalance`가 있으면 잔액도 표시합니다. 새 작업 성공, 이미 완료, 실패를 따로 표시하고 작업 목록으로 완료 상태를 확인합니다.

`loomy_login_result.json`에는 전화번호와 session, `loomy_onboarding.json`에는 작업 진행률과 단방향 session 지문이 저장됩니다. 둘 다 Git에서 제외됩니다. Issue에 session, 전화번호, 로컬 상태 파일을 공개하지 마세요.

## 사용 범위 및 재배포 안내

이 프로젝트의 공식 버전은 무료입니다. 저장소, 스크립트, 배포 안내와 Release 다운로드를 포함합니다.

저자의 명시적 서면 허가 없이 이 프로젝트를 유료 자료, 내부판, 독점판, 회원 혜택, 유료 강의, 유료 배포 또는 업데이트 서비스로 재포장하지 마세요. 무관한 계정, 그룹, 채널에 옮겨 트래픽이나 유입을 유도하거나, 저자 및 저작권 표시를 삭제하고 원작으로 주장하거나, 저자 이름, 아바타, QR 코드, 프로젝트 이름으로 공식 승인을 가장하는 행위도 금지됩니다.

위반 시 삭제 요청이 이뤄질 수 있으며, 저자는 업데이트를 중단하거나 저장소를 보관 또는 삭제할 수 있습니다. 전체 규칙은 [NOTICE.md](../NOTICE.md)를 확인하세요.

## 링크

- [Releases](https://github.com/L0NE-6/Loomy-Daily/releases)
- [Issues](https://github.com/L0NE-6/Loomy-Daily/issues)
- [소스와 전체 중국어 문서](../README.md)
