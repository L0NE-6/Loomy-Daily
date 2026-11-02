# 🌙 Loomy Daily

刷新 Loomy 每日贈送積分，並領取 8 項新手任務獎勵。專案以單一 Python 腳本運行，支援多帳號。

[简体中文](../README.md) · [English](README.en.md) · [繁體中文](README.zh-Hant.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Português (BR)](README.pt-BR.md)

完整中文文件請見 [../README.md](../README.md)。

## 核心能力

- 呼叫每日首次登入介面，以按天冪等方式刷新贈送積分。
- 逐項上報 8 個新手任務，完整進度合計 10000 分。
- 全部任務結清後寫入本機快照，後續預設不重複查詢。
- 提供 `--tasks`、`--claim KEY`、`--refresh` 進行查詢、單領與強制實查。
- 支援多 session、短信驗證碼登入與五種通知渠道。

## 青龍最短配置

```bash
python3 -m pip install -r requirements.txt
```

上傳 `loomy_daily.py`、設定 `LOOMY_TOKENS`，建立任務：

```text
45 8 * * * task loomy_daily.py
```

只刷新每日積分：

```text
45 8 * * * task loomy_daily.py --no-onboarding
```

取得 session：

```bash
python loomy_login.py
python loomy_login.py 13800000000 123456 --note 主號
python loomy_login.py --verify
```

## GitHub Actions

在 **Settings → Secrets and variables → Actions** 建立：

```text
LOOMY_TOKENS
PUSHPLUS_TOKEN          # 選填
BARK_URL                # 選填
WECOM_WEBHOOK           # 選填
DINGTALK_WEBHOOK        # 選填
DINGTALK_SECRET         # 選填
```

從 **Actions → Loomy Daily → Run workflow** 手動執行。預設僅手動觸發；需要排程時取消 `.github/workflows/daily.yml` 中 `schedule:` 的註解。cron 使用 UTC。

## 關鍵環境變數

| 變數 | 用途 |
| :--- | :--- |
| `LOOMY_TOKENS` | 必填。格式為 `session` 或 `備註\|session`；多帳號用換行或 `&` 分隔 |
| `LOOMY_ONBOARDING` | 預設 `1`；設為 `0` 可跳過新手任務 |
| `PUSHPLUS_TOKEN`、`BARK_URL`、`WECOM_WEBHOOK`、`DINGTALK_WEBHOOK`、`DINGTALK_SECRET` | 選填推送 |
| `QL_URL`、`QL_TOKEN` | 選填青龍通知位址與舊版面板 Token |

## 成功判據與隱私

每日介面返回業務碼 `000000` 才算刷新成功；有 `dailyBalance` 時會一併顯示。任務成功、此前已完成與失敗會分開標記，並以任務清單核對完成度。

`loomy_login_result.json` 含手機號與 session；`loomy_onboarding.json` 含任務進度與不可逆 session 指紋。兩者均被 Git 忽略。請勿在 Issue 公開 session、手機號或本機狀態檔。

## 使用邊界與轉載聲明

本專案的官方版本免費，包括倉庫、腳本、部署說明與 Release 下載。

未經作者明確書面許可，不得將本專案包裝為付費資源、內部版、獨家版、會員權益、收費課程、付費部署或包更新服務；不得搬運到無關帳號、群組或頻道進行漲粉、截流或引流；不得刪除作者與版權資訊後冒充原創；不得使用作者暱稱、頭像、收款碼或專案名稱製造官方授權背書假象。

違規時，作者可要求下架相關內容，並可暫停更新、封存或刪除倉庫。完整規則見 [NOTICE.md](../NOTICE.md)。

## 專案連結

- [Releases](https://github.com/L0NE-6/Loomy-Daily/releases)
- [Issues](https://github.com/L0NE-6/Loomy-Daily/issues)
- [原始碼與完整中文文件](../README.md)
