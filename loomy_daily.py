#!/usr/bin/env python3
"""
🌙 Loomy 每日签到 - 青龙脚本
------------------------------------------------------------

📌 功能
   Loomy 没有独立签到接口，它的「每日赠送积分」由每日首次登录触发：
   1. POST /api/v1/points/first-login          刷新每日赠送积分（按天幂等）
   2. GET  /api/v1/onboarding/tasks            读新手任务完成表
   3. POST /api/v1/onboarding/tasks/complete   逐个领取未完成任务（共 8 项 / 10000 分）
   新手任务默认领取，可用 --no-onboarding 或 LOOMY_ONBOARDING=0 关闭。

🔑 环境变量
   LOOMY_TOKENS     【必填】多账号用换行或 & 分隔：
       session
       备注|session
     session 为 Loomy 集成网关登录态（放 token 头，也放 Authorization: Bearer）
   LOOMY_ONBOARDING 【可选】1/0，是否领取新手任务，默认 1

   推送通道（均可选）：PUSHPLUS_TOKEN / BARK_URL / WECOM_WEBHOOK / DINGTALK_WEBHOOK / DINGTALK_SECRET

⌨️ 命令
   python loomy_daily.py                 签到 + 新手任务
   python loomy_daily.py --no-onboarding 只签到
   python loomy_daily.py --only 2        只跑第 2 个账号
   python loomy_daily.py --no-notify     不推送

📄 依赖：requests
"""
import base64
import hashlib
import hmac
import os
import sys
import time

import requests

import urllib3
urllib3.disable_warnings()

try:
    sys.stdout.reconfigure(errors="replace")
except Exception:
    pass

BASE = "https://loomyad.xunfei.cn"
FIRST_LOGIN_PATH = "/api/v1/points/first-login"
TASKS_PATH = "/api/v1/onboarding/tasks"
COMPLETE_PATH = "/api/v1/onboarding/tasks/complete"
SUCCESS_CODE = "000000"
AUTH_ERROR_CODES = ("020002", "100002")

TASKS = [
    ("first_message", "发送你的第一条消息", 500),
    ("pick_skill", "试试选择一个技能", 1000),
    ("generate_ppt", "生成第一份 PPT", 1500),
    ("set_schedule", "设置定时任务", 1000),
    ("install_skill", "在技能广场安装一个技能", 1500),
    ("configure_remote", "配置远程控制", 1000),
    ("create_soul", "创建你的第一个搭子", 1500),
    ("share_soul", "把搭子分享给朋友", 2000),
]

ONLY = None
NO_ONBOARDING = False
NO_NOTIFY = False


def log(msg):
    print("%s %s" % (time.strftime("[%H:%M:%S]"), msg), flush=True)


def mask(text, keep=6):
    text = str(text or "")
    if len(text) <= keep + 4:
        return text
    return text[:keep] + "****" + text[-4:]


def split_accounts(raw):
    out = []
    for chunk in (raw or "").replace("&", "\n").splitlines():
        chunk = chunk.strip().strip('"\'')
        if chunk and not chunk.startswith("#"):
            out.append(chunk)
    return out


def request(method, url, headers=None, body=None, timeout=20, retries=3):
    last = None
    for attempt in range(retries):
        try:
            session = requests.Session()
            session.trust_env = False
            return session.request(method, url, headers=headers or {},
                                   json=body if body is not None else None,
                                   timeout=timeout, verify=False)
        except Exception as error:
            last = error
            if attempt + 1 < retries:
                time.sleep(1.5 * (attempt + 1))
    raise RuntimeError("请求失败: %s" % last)


def json_of(response):
    try:
        return response.json()
    except Exception:
        return {}


def first_text(*values):
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
        if isinstance(value, (int, float)):
            return str(value)
    return ""


def token_headers(session_token):
    return {"token": session_token, "Authorization": "Bearer %s" % session_token}


def business_code(payload):
    return str(payload.get("code") or "").strip()


def upstream_message(payload):
    return first_text(payload.get("desc"), payload.get("message"))


# ---------- 上游协议 ----------

def first_login(session_token):
    response = request("POST", BASE + FIRST_LOGIN_PATH, headers=token_headers(session_token),
                       body={}, timeout=20)
    payload = json_of(response)
    code = business_code(payload)
    if response.status_code in (401, 403) or code in AUTH_ERROR_CODES:
        raise RuntimeError("登录状态失效，重新登录一下吧该账号")
    if code != SUCCESS_CODE:
        message = upstream_message(payload) or ("code=%s" % code)
        return False, "每日积分刷新失败：%s" % message
    balance = None
    data = payload.get("data")
    if isinstance(data, dict):
        balance = data.get("dailyBalance")
        if balance is None and isinstance(data.get("data"), dict):
            balance = data["data"].get("dailyBalance")
    return True, ("每日赠送积分已刷新（当前 %s）" % balance) if balance is not None else "每日赠送积分已刷新"


def fetch_done(session_token):
    response = request("GET", BASE + TASKS_PATH, headers=token_headers(session_token))
    payload = json_of(response)
    code = business_code(payload)
    if response.status_code in (401, 403) or code in AUTH_ERROR_CODES:
        raise RuntimeError("登录状态失效，重新登录一下吧该账号")
    if code != SUCCESS_CODE:
        raise RuntimeError("新手任务查询失败：%s" % (upstream_message(payload) or code))
    tasks = ((payload.get("data") or {}).get("tasks") or {}) if isinstance(payload.get("data"), dict) else {}
    return {key: tasks.get(key) is True for key, _, _ in TASKS}


def claim_task(session_token, key):
    response = request("POST", BASE + COMPLETE_PATH, headers=token_headers(session_token),
                       body={"key": key})
    payload = json_of(response)
    code = business_code(payload)
    if response.status_code in (401, 403) or code in AUTH_ERROR_CODES:
        raise RuntimeError("登录状态失效，重新登录一下吧该账号")
    if code != SUCCESS_CODE:
        return False, upstream_message(payload) or ("code=%s" % code)
    return True, ""


def claim_onboarding(session_token):
    done = fetch_done(session_token)
    newly, failed = [], []
    for key, title, points in TASKS:
        if done.get(key):
            continue
        try:
            ok, message = claim_task(session_token, key)
            if ok:
                newly.append("%s+%d" % (title, points))
            else:
                failed.append("%s(%s)" % (title, message[:40]))
        except Exception as error:
            failed.append("%s(%s)" % (title, str(error)[:40]))
        time.sleep(1.0)
    return newly, failed


def do_checkin(account):
    success, message = first_login(account["session"])
    if not success:
        return False, message
    parts = [message]
    if not NO_ONBOARDING:
        try:
            newly, failed = claim_onboarding(account["session"])
            if newly:
                parts.append("新手任务 +%d 项：%s" % (len(newly), "、".join(newly[:4])))
            elif failed:
                parts.append("新手任务待处理 %d 项" % len(failed))
            else:
                parts.append("新手任务已全部完成")
        except Exception as error:
            parts.append("新手任务查询失败：%s" % error)
    return True, "；".join(parts)


# ---------- 推送 ----------

def post_json(url, payload, timeout=20):
    session = requests.Session()
    session.trust_env = False
    return session.post(url, json=payload, timeout=timeout, verify=False)


def _env(name):
    return os.environ.get(name, "").strip()


def notify_pushplus(title, content):
    token = _env("PUSHPLUS_TOKEN")
    if not token:
        return False
    try:
        text = (content[:18000] + "\n...(已截断)") if len(content) > 18000 else content
        answer = post_json("https://www.pushplus.plus/send",
                           {"token": token, "title": title, "content": text, "template": "txt"})
        return str(json_of(answer).get("code")) == "200"
    except Exception:
        return False


def notify_bark(title, content):
    endpoint = _env("BARK_URL").rstrip("/")
    if not endpoint:
        return False
    try:
        answer = post_json(endpoint, {"title": title, "body": content, "group": "Loomy"})
        return json_of(answer).get("code") == 200
    except Exception:
        return False


def notify_wecom(title, content):
    hook = _env("WECOM_WEBHOOK")
    if not hook:
        return False
    if not hook.startswith("http"):
        hook = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=" + hook
    try:
        answer = post_json(hook, {"msgtype": "text",
                                  "text": {"content": ("%s\n%s" % (title, content))[:2000]}})
        return json_of(answer).get("errcode") == 0
    except Exception:
        return False


def notify_dingtalk(title, content):
    hook = _env("DINGTALK_WEBHOOK")
    if not hook:
        return False
    try:
        secret = _env("DINGTALK_SECRET")
        if secret:
            stamp = str(int(time.time() * 1000))
            digest = hmac.new(secret.encode(), ("%s\n%s" % (stamp, secret)).encode(),
                              hashlib.sha256).digest()
            hook += ("&" if "?" in hook else "?") + "timestamp=%s&sign=%s" % (
                stamp, requests.utils.quote(base64.b64encode(digest)))
        answer = post_json(hook, {"msgtype": "text",
                                  "text": {"content": "%s\n%s" % (title, content)}})
        return json_of(answer).get("errcode") == 0
    except Exception:
        return False


def notify_ql(title, content):
    try:
        from notify import send as panel_send
        panel_send(title, content)
        return True
    except Exception:
        pass
    endpoint = _env("QL_URL").rstrip("/")
    token = _env("QL_TOKEN")
    if not endpoint or not token:
        return False
    try:
        session = requests.Session()
        session.trust_env = False
        answer = session.post(endpoint + "/api/system/notify?token=" + token,
                              json={"title": title, "content": content}, timeout=15, verify=False)
        return str(json_of(answer).get("code")) in ("0", "200")
    except Exception:
        return False


def notify_all(title, content):
    handlers = (notify_pushplus, notify_bark, notify_wecom, notify_dingtalk, notify_ql)
    if not any(handler(title, content) for handler in handlers):
        log("（未配置推送渠道，本次只记录日志）")


# ---------- 账号解析与主流程 ----------

def parse_accounts(raw):
    accounts = []
    for index, line in enumerate(split_accounts(raw), 1):
        parts = [part.strip() for part in line.split("|")]
        if len(parts) >= 2:
            note, session_token = parts[0], parts[1]
        else:
            note, session_token = "账号%d" % index, parts[0]
        if session_token:
            accounts.append({"note": note or ("账号%d" % index), "session": session_token})
    return accounts


def main():
    global ONLY, NO_ONBOARDING, NO_NOTIFY
    args = sys.argv[1:]
    if "--no-onboarding" in args:
        NO_ONBOARDING = True
    if "--no-notify" in args:
        NO_NOTIFY = True
    if "--only" in args:
        try:
            ONLY = int(args[args.index("--only") + 1])
        except Exception:
            ONLY = None
    if os.environ.get("LOOMY_ONBOARDING", "1").strip() == "0":
        NO_ONBOARDING = True

    accounts = parse_accounts(os.environ.get("LOOMY_TOKENS", ""))
    if not accounts:
        log("❌ 未配置 LOOMY_TOKENS（多条用换行或 & 分隔；每条: session 或 备注|session）")
        return

    log("╔════════════════════════════════════╗")
    log("║ 🌙 Loomy 每日签到                  ║")
    log("╚════════════════════════════════════╝")
    log("👥 账号数: %d  新手任务领取: %s" % (len(accounts), "关闭" if NO_ONBOARDING else "开启"))

    report = []
    for index, account in enumerate(accounts, 1):
        if ONLY and index != ONLY:
            continue
        log("👤 [%d] %s  session=%s" % (index, account["note"], mask(account["session"])))
        try:
            success, message = do_checkin(account)
            log("   %s %s" % ("✅" if success else "ℹ️", message))
            report.append("账号%d %s: %s %s" % (index, account["note"], "✅" if success else "ℹ️", message))
        except Exception as error:
            log("   ❌ 异常: %s" % error)
            report.append("账号%d %s: ❌ %s" % (index, account["note"], error))
        time.sleep(1.5)

    summary = "🌙 Loomy 签到报告\n" + "\n".join(report) + "\n🕐 " + time.strftime("%Y-%m-%d %H:%M")
    log(summary)
    if not NO_NOTIFY:
        notify_all("🌙 Loomy 签到报告", summary)


if __name__ == "__main__":
    main()
