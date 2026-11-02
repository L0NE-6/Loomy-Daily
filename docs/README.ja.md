# 🌙 Loomy Daily

Loomy の毎日ギフトポイントを更新し、8 種類のオンボーディング課題報酬を取得する単一 Python スクリプトです。複数アカウントに対応します。

[简体中文](../README.md) · [English](README.en.md) · [繁體中文](README.zh-Hant.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Português (BR)](README.pt-BR.md)

完全な中国語ドキュメントは [../README.md](../README.md) を参照してください。

## 主な機能

- 毎日の初回ログイン API を呼び、ギフトポイントを日単位で冪等に更新します。
- 8 種類のオンボーディング課題を送信し、最大 10000 ポイントの進捗を追跡します。
- 全課題の精算後にローカル完了スナップショットを保存します。
- `--tasks`、`--claim KEY`、`--refresh` で確認、個別取得、強制再確認ができます。
- SMS コードログインと、改行または `&` 区切りの複数 session に対応します。
- PushPlus、Bark、WeCom、DingTalk、Qinglong 通知を利用できます。

## Qinglong 最小構成

```bash
python3 -m pip install -r requirements.txt
```

`loomy_daily.py` をアップロードし、`LOOMY_TOKENS` を設定してタスクを作成します。

```text
45 8 * * * task loomy_daily.py
```

オンボーディングを無効にする場合:

```text
45 8 * * * task loomy_daily.py --no-onboarding
```

session の作成:

```bash
python loomy_login.py
python loomy_login.py 13800000000 123456 --note main
python loomy_login.py --verify
```

## GitHub Actions

**Settings → Secrets and variables → Actions** で次の Secrets を作成します。

```text
LOOMY_TOKENS
PUSHPLUS_TOKEN          # 任意
BARK_URL                # 任意
WECOM_WEBHOOK           # 任意
DINGTALK_WEBHOOK        # 任意
DINGTALK_SECRET         # 任意
```

**Actions → Loomy Daily → Run workflow** から手動実行します。既定では手動のみです。スケジュールを使う場合は `.github/workflows/daily.yml` の `schedule:` を有効にしてください。cron は UTC です。

## 主要な環境変数

| 変数 | 用途 |
| :--- | :--- |
| `LOOMY_TOKENS` | 必須。`session` または `note\|session` 形式。複数アカウントは改行か `&` で区切ります |
| `LOOMY_ONBOARDING` | 既定値は `1`。`0` でオンボーディング処理を無効化 |
| `PUSHPLUS_TOKEN`、`BARK_URL`、`WECOM_WEBHOOK`、`DINGTALK_WEBHOOK`、`DINGTALK_SECRET` | 任意の通知設定 |
| `QL_URL`、`QL_TOKEN` | 任意の Qinglong 通知先と旧パネルトークン |

## 成功判定とプライバシー

日次 API が業務コード `000000` を返した場合に成功です。`dailyBalance` が返れば残高も表示します。課題の新規成功、既に完了、失敗は別々に表示し、課題一覧で完了状態を確認します。

`loomy_login_result.json` には電話番号と session、`loomy_onboarding.json` には課題進捗と一方向 session フィンガープリントが入ります。どちらも Git 対象外です。Issue に session、電話番号、ローカル状態ファイルを公開しないでください。

## リンク

- [Releases](https://github.com/L0NE-6/Loomy-Daily/releases)
- [Issues](https://github.com/L0NE-6/Loomy-Daily/issues)
- [ソースと完全な中国語ガイド](../README.md)
