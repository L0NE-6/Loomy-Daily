<div align="center">

<sub><strong>L0NE-6 · DAILY SIGNAL</strong></sub>

# 🌙 Loomy Daily

**刷新 Loomy 每日赠送积分，领取 8 项新手任务奖励，并用任务清单与积分增量双回读确认。**

> 当前版本：**v1.0.4**（2026-11-12） · 核心能力：每日首登积分、任务领取、done/earned 回读、多账号与短信登录

[简体中文](README.md) · [English](docs/README.en.md) · [繁體中文](docs/README.zh-Hant.md) · [日本語](docs/README.ja.md) · [한국어](docs/README.ko.md) · [Português (BR)](docs/README.pt-BR.md)

<p>
  <img src="https://img.shields.io/github/v/release/L0NE-6/Loomy-Daily?style=for-the-badge&label=Release&color=2ea44f&logo=github" alt="Release" />
  <img src="https://img.shields.io/github/stars/L0NE-6/Loomy-Daily?style=for-the-badge&label=Stars&color=FFC75F&logo=github" alt="Stars" />
  <img src="https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.8+" />
  <img src="https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20Qinglong-4EAA25?style=for-the-badge&logo=linux&logoColor=white" alt="Platform" />
  <img src="https://img.shields.io/github/license/L0NE-6/Loomy-Daily?style=for-the-badge&label=License&color=F472B6" alt="License" />
  <a href="https://github.com/L0NE-6/Loomy-Daily/releases"><img src="https://img.shields.io/badge/Download-Releases-2ea44f?style=for-the-badge&logo=github" alt="Download" /></a>
</p>

[🚫 使用边界](#usage-policy) · [✨ 30 秒速览](#overview) · [🧭 这是什么](#what-is-this) · [🔁 协议](#protocol) · [🔑 凭据](#credentials) · [🚀 本地](#local) · [🐧 青龙](#qinglong) · [☁️ Actions](#actions) · [⌨️ CLI](#cli-output) · [🧾 结果码](#result-codes) · [✅ 成功判据](#success) · [🧪 测试](#tests) · [🧱 设计原则](#design) · [🔒 隐私](#privacy) · [📁 目录](#layout) · [📦 版本](#release) · [⚠️ 免责声明](#disclaimer) · [☕ 赞赏](#donate) · [💬 反馈与 Star](#feedback)

</div>

---

<a id="usage-policy"></a>
## 🚫 使用边界与转载声明

> [!IMPORTANT]
> **官方版本永久免费。** 未经作者书面许可，禁止付费包装、搬运引流、冒充作者，或使用作者身份与二维码制造官方授权假象。

本项目仓库、脚本、部署说明和 Release 下载始终免费公开。未经作者明确书面许可，禁止将其包装为付费资源、内部版、独家版、会员权益、收费课程、付费部署或包更新服务；禁止搬运到其他账号、群组、频道、网盘、电商或付费平台进行涨粉、截流、倒卖和引流。

如需商业合作、品牌授权、联合分发或使用作者名义提供付费服务，请先取得作者明确书面授权。完整规则见 [NOTICE.md](NOTICE.md)。

---

<a id="overview"></a>
## ✨ 30 秒速览

| 维度 | 说明 |
| :--- | :--- |
| **做什么** | 刷新 Loomy 每日赠送积分，并领取已完成的新手任务奖励。 |
| **输入** | `LOOMY_TOKENS`；可选 `LOOMY_ONBOARDING=0` 关闭新手任务。 |
| **输出** | 分账号积分刷新状态、任务回读确认、累计进度、pending 和 unconfirmed 项。 |
| **部署** | Windows、Linux、青龙面板、GitHub Actions。 |
| **依赖** | Python 3.8+，仅 `requests`。 |
| **成功判据** | 每日接口返回 `000000`；任务必须 `done=true` 且 `earned` 增量匹配。 |

---

<a id="what-is-this"></a>
## 🧭 这是什么

Loomy 没有独立的传统签到接口，每日赠送积分由每日首次登录行为触发。脚本会：

1. 刷新每日赠送积分。
2. 读取 8 项新手任务状态。
3. 逐项上报未完成任务。
4. 再次读取任务清单与积分进度。
5. 只有任务状态和积分增量都确认后才标记成功。

全部任务结清后会写入本地快照，后续默认直接使用快照；`--refresh` 可强制实查。

---

<a id="protocol"></a>
## 🔁 协议、工作原理与回读

业务基址为 `https://loomyad.xunfei.cn`。

```text
POST /api/v1/points/first-login
GET  /api/v1/onboarding/tasks
POST /api/v1/onboarding/tasks/complete
GET  /api/v1/onboarding/tasks
```

执行顺序：

```text
每日首登积分
  → 任务清单 before
  → 逐项 complete
  → 任务清单 after
  → 比较 done=false → true
  → 比较 earned 增量
  → confirmed / pending / unconfirmed
```

上报成功但任务状态未变化标记为 `pending`；回读失败标记为 `unconfirmed`；两者都不计入已确认领取积分。

---

<a id="credentials"></a>
## 🔑 凭据与环境变量

多账号使用换行或 `&` 分隔。每条账号可写 `session` 或 `备注|session`，备注中不要包含 `|`。

| 变量 | 格式 | 说明 |
| :--- | :--- | :--- |
| `LOOMY_TOKENS` | `session` / `备注\|session` | 必填 |
| `LOOMY_ONBOARDING` | `1` / `0` | 是否领取新手任务，默认 `1` |
| `PUSHPLUS_TOKEN` / `BARK_URL` | Token / URL | 可选推送 |
| `WECOM_WEBHOOK` | Webhook 或 key | 企业微信 |
| `DINGTALK_WEBHOOK` / `DINGTALK_SECRET` | Webhook / 密钥 | 钉钉 |
| `QL_URL` / `QL_TOKEN` | 面板地址 / 旧版 Token | 青龙通知 |

短信登录：

```bash
python loomy_login.py
python loomy_login.py 13800000000 123456 --note 主号
python loomy_login.py --verify
```

工具使用同一次 `msgid` 完成发码与登录，输出 `备注|session`，并保存到本机 `loomy_login_result.json`。

---

<a id="local"></a>
## 🚀 本地快速开始

```bash
python -m pip install -r requirements.txt
```

配置：

```text
LOOMY_TOKENS=主号|SESSION_VALUE
```

运行：

```bash
python loomy_daily.py
python loomy_daily.py --only 1
python loomy_daily.py --tasks
```

只刷新每日积分：

```bash
python loomy_daily.py --no-onboarding
```

---

<a id="qinglong"></a>
## 🐧 青龙面板

1. 安装依赖：`python3 -m pip install -r requirements.txt`。
2. 上传 `loomy_daily.py`。
3. 设置 `LOOMY_TOKENS`。
4. 创建任务：

```text
# 每天北京时间 08:45
45 8 * * * task loomy_daily.py
```

只签到、不领取新手任务：

```text
45 8 * * * task loomy_daily.py --no-onboarding
```

---

<a id="actions"></a>
## ☁️ GitHub Actions

工作流位于 [`.github/workflows/daily.yml`](.github/workflows/daily.yml)。当前只启用 `workflow_dispatch`，定时段保持注释；示例 cron `45 0 * * *` 对应北京时间 08:45。

| Secret | 必填 | 说明 |
| :--- | :---: | :--- |
| `LOOMY_TOKENS` | 是 | 多账号 session |
| `PUSHPLUS_TOKEN` / `BARK_URL` | 可选 | PushPlus / Bark |
| `WECOM_WEBHOOK` | 可选 | 企业微信 |
| `DINGTALK_WEBHOOK` / `DINGTALK_SECRET` | 可选 | 钉钉与加签 |

Actions 不保留本地快照。需要长期使用 `--refresh` 或保留结清状态时，优先使用可持久化目录。

---

<a id="cli-output"></a>
## ⌨️ CLI 与输出

| 参数 | 作用 |
| :--- | :--- |
| 无 | 刷新每日积分并领取新手任务 |
| `--no-onboarding` | 只刷新每日积分 |
| `--tasks` | 只查看任务清单与进度 |
| `--claim KEY` | 单独上报并领取指定任务 |
| `--refresh` | 忽略本地结清快照，强制实查 |
| `--only 2` | 只跑第二个账号 |
| `--no-notify` | 关闭本轮推送 |

输出包含脱敏 session、每日积分状态、任务清单、已确认领取项、pending/unconfirmed 项和累计进度。

---

<a id="result-codes"></a>
## 🧾 结果码

| 结果 | 含义 |
| :--- | :--- |
| `confirmed` | 回读 `done=true` 且 earned 增量匹配 |
| `already_done` | 任务此前已完成 |
| `pending` | 上报已受理，但任务状态未变化 |
| `unconfirmed` | 回读失败或积分增量不足 |
| 业务码 `000000` | 每日首登积分接口成功 |
| 登录退出码 `0` / `1` / `130` | 成功 / 失败 / 用户中断 |
| 日任务进程退出码 `0` | 进程正常结束；逐账号结论以报告为准 |

---

<a id="success"></a>
## ✅ 成功判据

每日积分需要业务码 `000000`；服务端返回余额时同时展示 `dailyBalance`。

新手任务必须满足：

1. 领取前 `done=false`。
2. 领取后回读 `done=true`。
3. `earned` 增量不小于对应任务分值。

POST 成功、HTTP 200 或任务动作回执单独出现都不构成完成。

---

<a id="tests"></a>
## 🧪 测试

```bash
python -m unittest discover -s tests -v
python -m py_compile loomy_daily.py loomy_login.py
git diff --check
```

现有 6 项离线测试覆盖批量领取回读确认、无状态变化 pending、回读失败 unconfirmed、只统计已确认项、任务完成但积分增量不足、单条领取回读。

---

<a id="design"></a>
## 🧱 设计原则

- **前后双读**：领取前读取 before，领取后读取 after。
- **状态与积分双确认**：`done` 和 `earned` 同时校验。
- **幂等**：已完成任务不再上报。
- **本地结清快照**：8/8 完成后减少重复查询。
- **账号隔离**：单账号异常不阻断其他账号。
- **凭据最小暴露**：日志只显示脱敏 session。

---

<a id="privacy"></a>
## 🔒 隐私与数据边界

| 文件 | 内容 | 提交 |
| :--- | :--- | :---: |
| `loomy_login_result.json` | 手机号与 session | 否 |
| `loomy_onboarding.json` | 任务进度与不可逆 session 指纹 | 否 |

仓库不包含账号、手机号、session 或用户 ID。Issue 中请使用脱敏日志，不要粘贴 session、手机号或本地状态文件。

---

<a id="layout"></a>
## 📁 目录结构

```text
Loomy-Daily/
├── .github/workflows/daily.yml
├── assets/
├── docs/
├── tests/
├── loomy_daily.py
├── loomy_login.py
├── CHANGELOG.md
├── LICENSE
├── NOTICE.md
├── requirements.txt
└── README.md
```

---

<a id="release"></a>
## 📦 版本与发布

- 当前版本：`v1.0.4`，新增批量与单条领取的真实回读确认。
- 历史版本保留在 [Releases](https://github.com/L0NE-6/Loomy-Daily/releases)。
- 变更记录见 [CHANGELOG.md](CHANGELOG.md)。

---

<a id="disclaimer"></a>
## ⚠️ 免责声明

本项目用于个人学习与合法自动化实践。使用者应自行遵守 Loomy、科大讯飞及相关服务条款，并承担误配置、凭据泄露或账号异常带来的风险。

---

<a id="donate"></a>
## ☕ 支持与投喂：微信与支付宝赞赏码

脚本完全免费，赞赏纯自愿，不影响任何功能。

<p align="center">
  <img src="assets/donate-wechat.png" width="260" alt="微信赞赏码" />
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
  <img src="assets/donate-alipay.jpg" width="260" alt="支付宝收款码" />
</p>

<p align="center"><sub>微信支付（左） · 支付宝（右）</sub></p>

> [!WARNING]
> 收款码仅用于向作者自愿赞赏。任何第三方以代下载、代部署、内部资源、会员群或官方授权为由收费，均与作者无关。

---

<a id="feedback"></a>
## 💬 反馈与贡献：Star History

- [Issues](https://github.com/L0NE-6/Loomy-Daily/issues)
- [Pull Requests](https://github.com/L0NE-6/Loomy-Daily/pulls)
- [Releases](https://github.com/L0NE-6/Loomy-Daily/releases)

<a href="https://star-history.com/#L0NE-6/Loomy-Daily&Date">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=L0NE-6/Loomy-Daily&type=Date&theme=dark" />
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=L0NE-6/Loomy-Daily&type=Date&theme=light" />
    <img alt="Loomy Daily Star History" src="https://api.star-history.com/svg?repos=L0NE-6/Loomy-Daily&type=Date&theme=light" />
  </picture>
</a>

<div align="center">

[⭐ Star](https://github.com/L0NE-6/Loomy-Daily) · [🍴 Fork](https://github.com/L0NE-6/Loomy-Daily/fork) · L0NE-6 · DAILY SIGNAL

</div>
