<div align="center">

<sub><strong>L0NE-6 · DAILY SIGNAL</strong></sub>

# 🌙 Loomy Daily

**刷新 Loomy 每日赠送积分，并领取 8 项新手任务奖励的单文件自动化脚本。**

> 当前版本：**v1.0.4**（2026-11-13） · 最新更新：批量与单条领取均执行领取前后任务清单回读

[简体中文](README.md) · [English](docs/README.en.md) · [繁體中文](docs/README.zh-Hant.md) · [日本語](docs/README.ja.md) · [한국어](docs/README.ko.md) · [Português (BR)](docs/README.pt-BR.md)

<p>
  <img src="https://img.shields.io/github/v/release/L0NE-6/Loomy-Daily?style=for-the-badge&label=Release&color=2ea44f&logo=github" alt="Release" />
  <img src="https://img.shields.io/github/stars/L0NE-6/Loomy-Daily?style=for-the-badge&label=Stars&color=FFC75F&logo=github" alt="Stars" />
  <img src="https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.8+" />
  <img src="https://img.shields.io/badge/%E9%9D%92%E9%BE%99-%E5%8D%95%E6%96%87%E4%BB%B6-4EAA25?style=for-the-badge" alt="Qinglong" />
  <img src="https://img.shields.io/badge/GitHub%20Actions-Supported-2088FF?style=for-the-badge&logo=githubactions&logoColor=white" alt="GitHub Actions" />
  <img src="https://img.shields.io/badge/License-MIT-F472B6?style=for-the-badge" alt="MIT License" />
  <a href="https://github.com/L0NE-6/Loomy-Daily/releases"><img src="https://img.shields.io/badge/%E2%AC%87%20Download-Releases-2ea44f?style=for-the-badge&logo=github" alt="Download Releases" /></a>
</p>

[✨ 30 秒速览](#quick-overview) · [🚀 青龙部署](#quick-boot) · [☁️ Actions](#actions) · [🔐 获取 Session](#credentials) · [🔧 环境变量](#environment) · [✅ 成功判据](#result) · [❓ FAQ](#faq) · [🚫 使用边界](#usage-policy) · [✦ 星轨](#star-trail)

</div>

---

<a id="quick-overview"></a>

<a id="usage-policy"></a>
## 🚫 使用边界与转载声明

> [!IMPORTANT]
> **官方版本永久免费。** 未经作者书面许可，禁止付费包装、搬运引流、冒充作者，或使用作者身份与二维码制造官方授权假象。违规内容可能被要求下架；作者可暂停更新、归档或删除仓库及相关 Release。

本项目仓库、脚本、部署说明和 Release 下载始终免费公开。未经作者明确书面许可，禁止将本项目包装为付费资源、内部版、独家版、会员权益、收费课程、付费部署或包更新服务；禁止搬运到其他账号、群组、频道、网盘、电商或付费平台进行涨粉、截流、倒卖和引流；禁止删除作者与版权信息后冒充原创；禁止使用作者昵称、头像、二维码和项目名称制造官方授权假象。

> 如需商业合作、品牌授权、联合分发或使用作者名义提供付费服务，请先取得作者明确书面授权。完整规则、收款码防诈骗说明和违规处理方式见 **[NOTICE.md](NOTICE.md)**。

> 官方仓库和 Release 始终免费。第三方以“下载费 / 激活费 / 内部版 / 代部署 / 会员门槛”等名义收费，均与作者无关，请停止付款并保留证据。

> 对上述违规行为，作者有权要求立即停止传播、删除内容并下架相关商品或页面；并可视情况暂停更新、归档或删除本仓库及相关 Release、向平台投诉或采取进一步必要措施。

<a id="support"></a>

---

## ✨ 30 秒速览

| 维度 | 说明 |
| :--- | :--- |
| **用途** | 刷新 Loomy 每日赠送积分，并领取已完成的新手任务奖励。 |
| **输入** | `LOOMY_TOKENS`；可选 `LOOMY_ONBOARDING=0` 关闭新手任务。 |
| **输出** | 分账号积分刷新状态、任务回读确认、累计进度与 `pending` / `unconfirmed` 项。 |
| **部署** | 青龙面板、GitHub Actions，或本地 Python 运行。 |
| **依赖** | Python 3.8+，仅需 `requests`。 |
| **成功判据** | 每日接口返回业务码 `000000` 并确认积分刷新；任务必须二次回读确认 `done=true` 且积分增量匹配。 |

<a id="signals"></a>

## 🎯 核心能力

- ✅ **每日积分刷新**：调用每日首次登录接口，按天幂等刷新赠送积分。
- 🎁 **新手任务领取**：逐项上报 8 个任务，领取后重新读取任务清单与积分增量，确认到账后才标记成功。
- 🧾 **本地结清记录**：8 项全部结清后写本机快照，之后默认不再重复查询。
- 🔍 **任务诊断**：`--tasks` 查看清单与进度，`--claim KEY` 单独处理某个任务。
- ♻️ **强制实查**：`--refresh` 忽略本地结清快照并重新读取上游。
- 📱 **短信登录**：手机号与验证码直接换取 session。
- 👥 **多账号与推送**：支持换行 / `&` 分隔账号，以及五种通知渠道。

## 🧩 工作方式

```text
POST /api/v1/points/first-login
GET  /api/v1/onboarding/tasks
POST /api/v1/onboarding/tasks/complete
GET  /api/v1/onboarding/tasks
```

Loomy 没有独立的传统签到接口，“每日赠送积分”由每日首次登录行为触发。新手任务默认随签到一并领取；上报后的第二次 GET 才是成功依据，任务状态未变化会标记为 `pending`，回读失败会标记为 `unconfirmed`。重复运行只处理未结清项，不会重复加分。

## 📦 文件说明

| 文件 | 用途 |
| :--- | :--- |
| `loomy_login.py` | 手机号 + 短信验证码登录，输出 `备注\|session` |
| `loomy_daily.py` | 每日积分刷新与新手任务领取 |
| `requirements.txt` | Python 依赖清单 |

<a id="quick-boot"></a>

## 🚀 青龙部署

1. 安装依赖：`python3 -m pip install -r requirements.txt`。
2. 上传 `loomy_daily.py` 到青龙「脚本管理」。
3. 在「环境变量」添加 `LOOMY_TOKENS`。
4. 使用青龙运行器建立定时任务。

```text
# 每天北京时间 08:45
45 8 * * * task loomy_daily.py
```

只签到、不领取新手任务：

```text
45 8 * * * task loomy_daily.py --no-onboarding
```

或在青龙环境变量中设置 `LOOMY_ONBOARDING=0`。

<a id="actions"></a>

## ☁️ GitHub Actions

1. Fork 或导入仓库到自己的账号。
2. 在 **Settings → Secrets and variables → Actions** 新建 Secrets。
3. 从 **Actions → Loomy Daily → Run workflow** 手动验证。
4. 默认仅手动触发；需要定时时，在 `.github/workflows/daily.yml` 取消 `schedule:` 两行注释。cron 使用 UTC。

| Secret | 必填 | 说明 |
| :--- | :---: | :--- |
| `LOOMY_TOKENS` | 是 | 多账号 session |
| `PUSHPLUS_TOKEN` / `BARK_URL` | 可选 | PushPlus / Bark |
| `WECOM_WEBHOOK` / `DINGTALK_WEBHOOK` / `DINGTALK_SECRET` | 可选 | 企业微信 / 钉钉 |

<a id="credentials"></a>

## 🔐 获取 Session

```bash
python loomy_login.py
python loomy_login.py 13800000000 123456 --note 主号
python loomy_login.py --verify
```

工具使用同一次 `msgid` 完成发码与登录，输出一行 `备注|session`，保存到本机 `loomy_login_result.json`。也可以从桌面端集成网关请求的 `token` 头取得 session。

Session 通常约 14 天失效。失效后重新登录并替换 `LOOMY_TOKENS` 中对应账号即可。

<a id="environment"></a>

## 🔧 环境变量与参数

多账号使用换行或 `&` 分隔。每条账号可写 `session` 或 `备注|session`，备注中不要包含 `|`。

| 环境变量 | 格式 | 说明 |
| :--- | :--- | :--- |
| `LOOMY_TOKENS` | `session` / `备注\|session` | 必填，多账号换行或 `&` |
| `LOOMY_ONBOARDING` | `1` / `0` | 是否领取新手任务，默认 `1` |
| `PUSHPLUS_TOKEN` / `BARK_URL` | Token / URL | 可选推送 |
| `WECOM_WEBHOOK` / `DINGTALK_WEBHOOK` / `DINGTALK_SECRET` | Webhook / 加签密钥 | 可选推送 |
| `QL_URL` / `QL_TOKEN` | 面板地址 / 旧版面板 Token | 可选青龙通知 |

| 参数 | 作用 |
| :--- | :--- |
| `--no-onboarding` | 只刷新每日积分，不领新手任务 |
| `--tasks` | 只查看任务清单与进度 |
| `--claim KEY` | 单独上报并领取指定任务 |
| `--refresh` | 忽略本地结清快照，强制实查 |
| `--only 2` | 只跑第 2 个账号 |
| `--no-notify` | 关闭本轮推送 |

<a id="result"></a>

## ✅ 成功判据与输出

- 每日积分接口必须返回业务码 `000000`，有余额时报告服务端返回的 `dailyBalance`。
- 新手任务逐项上报后会重新 GET 任务清单；只有 `done=true` 且 `earned` 增量匹配才标记成功。
- 回读无变化标记为 `pending`，回读失败标记为 `unconfirmed`，两者都不计入已确认领取积分。
- 任务清单与本地结算快照用于判断是否全部结清，不把单个 POST 成功或 HTTP 200 当作任务完成。
- 登录失效会明确提示重新登录，不持续用坏 session 空跑。

```text
[08:45:01] 👤 [1] 主号  session=abc1****wxyz
[08:45:02]    ✅ 每日赠送积分已刷新（当前 5000）；新手任务 +2 项：发送你的第一条消息+500、试试选择一个技能+1000
```

<a id="data-privacy"></a>

## 🗂️ 数据文件与隐私

| 文件 | 内容 | 是否提交 |
| :--- | :--- | :---: |
| `loomy_login_result.json` | 登录记录，含手机号与 session | 否，已忽略 |
| `loomy_onboarding.json` | 任务进度与不可逆 session 指纹 | 否，已忽略 |

- 仓库不内置账号、手机号、session 或用户 ID。
- 凭据由环境变量或 GitHub Secrets 注入。
- Issue 中请使用脱敏日志，不要粘贴 session、手机号或本地状态文件。

<a id="faq"></a>

## ❓ 常见问题

**session 多久过期？**
登录请求按 14 天有效期申请 session；失效后重新执行 `loomy_login.py`。

**验证码收不到？**
避免连续快速发码，稍后重试或更换时间段。

**新手任务都会自动领吗？**
脚本会逐项上报 8 个任务，然后重新读取任务清单与积分进度；只有状态和积分增量都确认才记为成功。全部结清后写入本机；误删记录或想强制实查时使用 `--refresh`。

**为什么显示“已结清”但没有请求？**
本机快照记录到 8/8 已完成。默认直接使用快照，`--refresh` 可重新读取上游。

<a id="release"></a>

## 📦 版本与发布
- 当前发布版：`v1.0.4`（2026-11-12，新手任务真实回读确认）。

当前 CHANGELOG 记录最新版本为 `v1.0.3`（2026-11-04）。每个版本单独发布 Release，附完整包、脚本单文件与 `SHA256SUMS.txt`。下载页：[Releases](https://github.com/L0NE-6/Loomy-Daily/releases)。

## ⚠️ 说明

本项目用于学习与个人自动化。请遵守对应平台的服务条款，并自行承担运行风险。

## ☕ 支持与反馈

脚本完全免费，支持不影响任何功能。

- [提交 Issue](https://github.com/L0NE-6/Loomy-Daily/issues)：请附运行日志、复现步骤与脱敏后的错误。
- [发起 Pull Request](https://github.com/L0NE-6/Loomy-Daily/pulls)：欢迎修复、测试与文档贡献。
- [点一个 Star](https://github.com/L0NE-6/Loomy-Daily)：让更多使用者找到这个项目。

<p align="center">
  <img src="assets/donate-wechat.png" width="240" alt="微信赞赏码" />
  &nbsp;&nbsp;&nbsp;&nbsp;
  <img src="assets/donate-alipay.jpg" width="240" alt="支付宝收款码" />
</p>
<p align="center"><sub>微信支付（左） · 支付宝（右）</sub></p>

> ⚠️ 收款码仅用于向作者自愿赞赏。任何第三方以代下载、代部署、内部资源或会员群为由收费，均与作者无关，请停止付款并保留证据。

<a id="star-trail"></a>

## ✦ 星轨 Star Trail

> 每日积分像月相循环，稳定的自动化则让每一轮都留下可回看的轨迹。

<a href="https://star-history.com/#L0NE-6/Loomy-Daily&Date">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=L0NE-6/Loomy-Daily&type=Date&theme=dark" />
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=L0NE-6/Loomy-Daily&type=Date&theme=light" />
    <img alt="Loomy Daily Star Trail" src="https://api.star-history.com/svg?repos=L0NE-6/Loomy-Daily&type=Date&theme=light" />
  </picture>
</a>

---

<div align="center">
  <sub>L0NE-6 · DAILY SIGNAL</sub>
  <br />
  <a href="https://github.com/L0NE-6/Loomy-Daily/releases">Releases</a>
  ·
  <a href="https://github.com/L0NE-6/Loomy-Daily/issues">Issues</a>
  ·
  <a href="https://github.com/L0NE-6/Loomy-Daily">Star</a>
</div>
