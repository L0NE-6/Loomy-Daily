# 🌙 Loomy Daily

Refreshes the daily Loomy gift points and claims rewards for the eight onboarding tasks. The automation is contained in one Python script and supports multiple accounts.

[简体中文](../README.md) · [English](README.en.md) · [繁體中文](README.zh-Hant.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Português (BR)](README.pt-BR.md)

For the complete Chinese documentation, see [../README.md](../README.md).

## Highlights

- Calls the daily first-login endpoint to refresh gift points idempotently.
- Submits the eight onboarding tasks and tracks up to 10000 points.
- Stores a local completion snapshot after all tasks are settled.
- Provides `--tasks`, `--claim KEY`, and `--refresh` for inspection and recovery.
- Supports SMS-code login and multiple sessions separated by newline or `&`.
- Supports PushPlus, Bark, WeCom, DingTalk, and Qinglong notifications.

## Qinglong Quick Start

```bash
python3 -m pip install -r requirements.txt
```

Upload `loomy_daily.py`, configure `LOOMY_TOKENS`, and create this task:

```text
45 8 * * * task loomy_daily.py
```

Disable onboarding claims when needed:

```text
45 8 * * * task loomy_daily.py --no-onboarding
```

To create a session:

```bash
python loomy_login.py
python loomy_login.py 13800000000 123456 --note main
python loomy_login.py --verify
```

## GitHub Actions

Create these repository secrets under **Settings → Secrets and variables → Actions**:

```text
LOOMY_TOKENS
PUSHPLUS_TOKEN          # optional
BARK_URL                # optional
WECOM_WEBHOOK           # optional
DINGTALK_WEBHOOK        # optional
DINGTALK_SECRET         # optional
```

Run **Actions → Loomy Daily → Run workflow**. The workflow is manual by default. Enable the commented schedule in `.github/workflows/daily.yml` when needed; cron uses UTC.

## Key Environment Variables

| Variable | Meaning |
| :--- | :--- |
| `LOOMY_TOKENS` | Required. Use `session` or `note\|session`; separate accounts by newline or `&`. |
| `LOOMY_ONBOARDING` | `1` by default. Set `0` to skip onboarding rewards. |
| `PUSHPLUS_TOKEN`, `BARK_URL`, `WECOM_WEBHOOK`, `DINGTALK_WEBHOOK`, `DINGTALK_SECRET` | Optional notification channels |
| `QL_URL`, `QL_TOKEN` | Optional Qinglong notification endpoint and legacy panel token |

## Success and Privacy

The daily gift is successful when the API returns business code `000000`; the script reports `dailyBalance` when available. Task success, an already-completed task, and a failure are reported separately, and completion is checked against the task list.

`loomy_login_result.json` contains a phone number and session. `loomy_onboarding.json` contains task progress and a one-way session fingerprint. Both are ignored by Git. Never paste a session, phone number, or local state file into an issue.

## Usage and redistribution

Official versions of this project are free, including the repository, scripts, deployment instructions, and Releases.

Without explicit written permission from the author, do not repackage the project as a paid resource, internal or exclusive edition, membership benefit, paid course, paid deployment, or update service; do not repost it to unrelated accounts, groups, or channels for traffic or lead generation; do not remove author or copyright notices or claim the work as your own; do not use the author's name, avatar, QR codes, or project name to imply official endorsement.

Violations may result in a takedown request. The author may pause updates, archive, or remove the repository. See [NOTICE.md](../NOTICE.md) for the complete rules.

## Project Links

- [Releases](https://github.com/L0NE-6/Loomy-Daily/releases)
- [Issues](https://github.com/L0NE-6/Loomy-Daily/issues)
- [Source and complete Chinese guide](../README.md)
