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
   8 项全部领完后会把结算记录写在本机，之后不再重复查询；--refresh 可强制实查。

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
   python loomy_daily.py --tasks         只看任务清单与进度
   python loomy_daily.py --claim KEY     单独领取某个任务
   python loomy_daily.py --refresh       忽略本地结算记录，强制实查
   python loomy_daily.py --only 2        只跑第 2 个账号
   python loomy_daily.py --no-notify     不推送

📄 依赖：requests
"""
import base64
import hashlib
import hmac
import json
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

STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "loomy_onboarding.json")
TOTAL_POINTS = 10000

TASKS = [
    ("初识 Loomy", "first_message", "发送你的第一条消息", 500),
    ("初识 Loomy", "pick_skill", "试试选择一个技能", 1000),
    ("初识 Loomy", "generate_ppt", "生成第一份 PPT", 1500),
    ("打造你的专属 Loomy", "set_schedule", "设置定时任务", 1000),
    ("打造你的专属 Loomy", "install_skill", "在技能广场安装一个技能", 1500),
    ("打造你的专属 Loomy", "configure_remote", "配置远程控制", 1000),
    ("遇见你的 AI 搭子", "create_soul", "创建你的第一个搭子", 1500),
    ("遇见你的 AI 搭子", "share_soul", "把搭子分享给朋友", 2000),
]

ONLY = None
NO_ONBOARDING = False
NO_NOTIFY = False
FORCE_REFRESH = False


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


def token_fp(session_token):
    return hashlib.sha256(session_token.encode("utf-8")).hexdigest()[:16]


# ---------- 新手任务结算记录（一次性福利，领完不再重复查询） ----------

def load_state():
    try:
        with open(STATE_FILE, encoding="utf-8") as handle:
            data = json.load(handle)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def save_state(state):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as handle:
            json.dump(state, handle, ensure_ascii=False, indent=2)
    except Exception as error:
        log("⚠️ 新手任务结算记录写入失败: %s" % error)


def settled_snapshot(state, session_token):
    snapshot = state.get(token_fp(session_token))
    return snapshot if isinstance(snapshot, dict) else None


def settled_view(snapshot):
    return {"tasks": snapshot.get("tasks"), "earned": snapshot.get("earned"),
            "total": snapshot.get("total"), "unclaimed": 0, "settled": True,
            "settledAt": snapshot.get("at"), "fromMemory": True}


def remember(state, session_token, payload, previous):
    """按响应结论同步本地记录：结清就记住，出现待领就清掉旧记录。"""
    fingerprint = token_fp(session_token)
    if payload.get("settled"):
        at = previous.get("at") if previous and previous.get("tasks") == payload.get("tasks") else None
        if not isinstance(at, (int, float)):
            at = int(time.time() * 1000)
        state[fingerprint] = {"at": at, "tasks": payload.get("tasks"),
                              "earned": payload.get("earned"), "total": payload.get("total")}
        save_state(state)
        payload["settledAt"] = at
    elif fingerprint in state:
        del state[fingerprint]
        save_state(state)


def task_rows(done):
    rows, earned, unclaimed = [], 0, 0
    for group, key, title, points in TASKS:
        is_done = bool(done.get(key))
        if is_done:
            earned += points
        else:
            unclaimed += 1
        rows.append({"key": key, "title": title, "group": group,
                     "points": points, "done": is_done})
    return rows, earned, unclaimed


def fetch_onboarding(session_token):
    """查询任务清单与进度：key / 标题 / 分组 / 分值 / 是否完成，一次只读。"""
    response = request("GET", BASE + TASKS_PATH, headers=token_headers(session_token))
    payload = json_of(response)
    code = business_code(payload)
    if response.status_code in (401, 403) or code in AUTH_ERROR_CODES:
        raise RuntimeError("登录状态失效，重新登录一下吧该账号")
    if code != SUCCESS_CODE:
        raise RuntimeError("新手任务查询失败：%s" % (upstream_message(payload) or code))
    raw = ((payload.get("data") or {}).get("tasks") or {}) if isinstance(payload.get("data"), dict) else {}
    done = {key: raw.get(key) is True for _group, key, _title, _points in TASKS}
    rows, earned, unclaimed = task_rows(done)
    return {"tasks": rows, "earned": earned, "total": TOTAL_POINTS,
            "unclaimed": unclaimed, "settled": unclaimed == 0}


def claim_task(session_token, key):
    """上报单个任务 key。返回 (成功, 此前已完成, 失败原因)。"""
    response = request("POST", BASE + COMPLETE_PATH, headers=token_headers(session_token),
                       body={"key": key})
    payload = json_of(response)
    code = business_code(payload)
    if response.status_code in (401, 403) or code in AUTH_ERROR_CODES:
        raise RuntimeError("登录状态失效，重新登录一下吧该账号")
    if code != SUCCESS_CODE:
        return False, False, upstream_message(payload) or ("code=%s" % code)
    data = payload.get("data")
    already = bool(isinstance(data, dict) and data.get("alreadyCompleted") is True)
    return True, already, ""


def onboarding_view(session_token, refresh=False):
    """清单查询入口：已结清直接给本地记录（零请求），否则实查并同步记录。"""
    state = load_state()
    previous = settled_snapshot(state, session_token)
    if previous and not refresh:
        return settled_view(previous)
    payload = fetch_onboarding(session_token)
    remember(state, session_token, payload, previous)
    return payload


def claim_onboarding(session_token, refresh=False):
    """一键领取未完成任务。返回 (新到账摘要, 失败列表, 明细)。"""
    state = load_state()
    previous = settled_snapshot(state, session_token)
    if previous and not refresh:
        return [], [], settled_view(previous)
    before = fetch_onboarding(session_token)
    done = {row["key"]: row["done"] for row in before["tasks"]}
    newly, failed, results = [], [], []
    claimed_points = 0
    for _group, key, title, points in TASKS:
        if done.get(key):
            continue
        try:
            ok, already, message = claim_task(session_token, key)
        except Exception as error:
            failed.append("%s(%s)" % (title, str(error)[:40]))
            results.append({"key": key, "ok": False, "error": str(error)[:80]})
            time.sleep(1.0)
            continue
        if not ok:
            failed.append("%s(%s)" % (title, message[:40]))
            results.append({"key": key, "ok": False, "error": message[:80]})
            time.sleep(1.0)
            continue
        done[key] = True
        claimed_points += points
        results.append({"key": key, "ok": True, "already": already, "points": points})
        newly.append("%s（此前已完成）" % title if already else "%s+%d" % (title, points))
        time.sleep(1.0)
    rows, earned, unclaimed = task_rows(done)
    payload = {"results": results,
               "claimed": len([row for row in results if row.get("ok")]),
               "failed": len(failed), "claimedPoints": claimed_points,
               "tasks": rows, "earned": earned, "total": TOTAL_POINTS,
               "unclaimed": unclaimed, "settled": unclaimed == 0}
    remember(state, session_token, payload, None)
    return newly, failed, payload


def claim_single(session_token, key, refresh=False):
    """单独领取某个 key（幂等上报，不依赖清单里那一行是否勾选）。"""
    state = load_state()
    previous = settled_snapshot(state, session_token)
    if previous and not refresh:
        return settled_view(previous)
    ok, already, message = claim_task(session_token, key)
    payload = {"key": key, "ok": ok, "already": already, "error": message}
    if ok:
        try:
            view = fetch_onboarding(session_token)
            remember(state, session_token, view, previous)
            payload.update(view)
        except Exception as error:
            payload["refreshError"] = str(error)[:80]
    return payload


def log_task_list(payload):
    log("   📋 新手任务进度：已得 %s / %s，待领 %s%s"
        % (payload.get("earned"), payload.get("total"), payload.get("unclaimed"),
           "（本地结算记录）" if payload.get("fromMemory") else ""))
    for row in payload.get("tasks") or []:
        log("      %s [%s] %s +%s" % ("✅" if row.get("done") else "⬜",
                                       row.get("group", ""), row.get("title"),
                                       row.get("points")))


def do_checkin(account):
    success, message = first_login(account["session"])
    if not success:
        return False, message
    parts = [message]
    if not NO_ONBOARDING:
        try:
            newly, failed, payload = claim_onboarding(account["session"], refresh=FORCE_REFRESH)
            earned = payload.get("earned")
            total = payload.get("total")
            if payload.get("settled") and not failed:
                if newly:
                    parts.append("新手任务 +%d 项：%s（累计 %s/%s）"
                                 % (len(newly), "、".join(newly[:4]), earned, total))
                elif payload.get("fromMemory"):
                    parts.append("新手任务已结清（本地记录，累计 %s/%s）" % (earned, total))
                else:
                    parts.append("新手任务已全部完成（累计 %s/%s）" % (earned, total))
            elif failed:
                parts.append("新手任务待处理 %d 项（失败 %d 项）"
                             % (payload.get("unclaimed", 0), len(failed)))
            else:
                parts.append("新手任务待处理 %d 项" % payload.get("unclaimed", 0))
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
    global ONLY, NO_ONBOARDING, NO_NOTIFY, FORCE_REFRESH
    args = sys.argv[1:]
    if "--no-onboarding" in args:
        NO_ONBOARDING = True
    if "--no-notify" in args:
        NO_NOTIFY = True
    if "--refresh" in args:
        FORCE_REFRESH = True
    if "--only" in args:
        try:
            ONLY = int(args[args.index("--only") + 1])
        except Exception:
            ONLY = None
    if os.environ.get("LOOMY_ONBOARDING", "1").strip() == "0":
        NO_ONBOARDING = True

    mode = "checkin"
    claim_key = ""
    if "--tasks" in args:
        mode = "tasks"
    if "--claim" in args:
        try:
            claim_key = args[args.index("--claim") + 1].strip()
        except Exception:
            claim_key = ""
        if claim_key:
            mode = "claim"
        else:
            log("⚠️ --claim 需要跟一个任务 key，本次按默认签到执行")

    accounts = parse_accounts(os.environ.get("LOOMY_TOKENS", ""))
    if not accounts:
        log("❌ 未配置 LOOMY_TOKENS（多条用换行或 & 分隔；每条: session 或 备注|session）")
        return

    log("╔════════════════════════════════════╗")
    log("║ 🌙 Loomy 每日签到                  ║")
    log("╚════════════════════════════════════╝")
    if mode == "checkin":
        mode_label = "只签到" if NO_ONBOARDING else "签到 + 新手任务"
    elif mode == "tasks":
        mode_label = "任务清单查询"
    else:
        mode_label = "单条领取（%s）" % claim_key
    log("👥 账号数: %d  运行模式: %s" % (len(accounts), mode_label))

    report = []
    for index, account in enumerate(accounts, 1):
        if ONLY and index != ONLY:
            continue
        log("👤 [%d] %s  session=%s" % (index, account["note"], mask(account["session"])))
        try:
            if mode == "tasks":
                payload = onboarding_view(account["session"], refresh=FORCE_REFRESH)
                log_task_list(payload)
                report.append("账号%d %s: 📋 已得 %s/%s，待领 %s"
                              % (index, account["note"], payload.get("earned"),
                                 payload.get("total"), payload.get("unclaimed")))
            elif mode == "claim":
                payload = claim_single(account["session"], claim_key, refresh=FORCE_REFRESH)
                if payload.get("fromMemory"):
                    log("   ℹ️ 已结清（本地记录），未重复上报")
                    report.append("账号%d %s: ℹ️ 新手任务已结清" % (index, account["note"]))
                elif payload.get("ok"):
                    tail = "（此前已完成）" if payload.get("already") else ""
                    log("   ✅ 已上报 %s%s" % (claim_key, tail))
                    report.append("账号%d %s: ✅ %s%s" % (index, account["note"], claim_key, tail))
                else:
                    log("   ❌ %s 领取失败: %s" % (claim_key, payload.get("error") or "未知错误"))
                    report.append("账号%d %s: ❌ %s 领取失败" % (index, account["note"], claim_key))
            else:
                success, message = do_checkin(account)
                log("   %s %s" % ("✅" if success else "ℹ️", message))
                report.append("账号%d %s: %s %s" % (index, account["note"], "✅" if success else "ℹ️", message))
        except Exception as error:
            log("   ❌ 异常: %s" % error)
            report.append("账号%d %s: ❌ %s" % (index, account["note"], error))
        time.sleep(1.5)

    title = "🌙 Loomy 签到报告" if mode == "checkin" else "🌙 Loomy 任务报告"
    summary = title + "\n" + "\n".join(report) + "\n🕐 " + time.strftime("%Y-%m-%d %H:%M")
    log(summary)
    if not NO_NOTIFY:
        notify_all(title, summary)


if __name__ == "__main__":
    main()
