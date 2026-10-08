#!/usr/bin/env python3
"""
📱 Loomy 短信验证码登录工具
------------------------------------------------------------
输入手机号 → 发送验证码 → 输入验证码 → 直接拿到 session

用法:
  python loomy_login.py                      # 交互式登录
  python loomy_login.py PHONE          # 指定手机号
  python loomy_login.py PHONE CODE   # 指定手机号和验证码
  python loomy_login.py --note 小号A         # 指定备注名（写进环境变量行）
  python loomy_login.py --verify             # 登录后校验 session 可用性

输出（直接作为 LOOMY_TOKENS 的一行）:
  备注|session

仅依赖 requests。
"""
import base64
import hashlib
import hmac
import json
import os
import re
import sys
import time
import uuid
from email.utils import formatdate

import requests

import urllib3
urllib3.disable_warnings()

try:
    sys.stdout.reconfigure(errors="replace")
except Exception:
    pass

BASE = "https://account.xfinfr.com"
SEND_CODE_PATH = "/login/phone/sendMsgCode"
LOGIN_PATH = "/login/phone/checkCode"
TASKS_PATH = "/api/v1/onboarding/tasks"
INTEGRATION_BASE = "https://loomyad.xunfei.cn"

ACCESS_KEY_ID = "2thryby66wxi53sk"
ACCESS_KEY_SECRET = "zsak6eadrbawz683wf5r3m2snrwj868r"
APP_ID = "GM3LOOMY"
MODEL_ID = "Web"
DEVICE_ID = "web"
CLIENT_UA = "Loomy|Desktop|Electron|macOS"
CLIENT_VERSION = "1.0.0"
SUCCESS_CODE = "000000"


def log(msg):
    print("%s %s" % (time.strftime("[%H:%M:%S]"), msg), flush=True)


def mask_phone(phone):
    phone = str(phone or "")
    return phone[:3] + "****" + phone[-4:] if len(phone) >= 7 else phone


def normalize_phone(raw):
    text = re.sub(r"[\s\-]", "", str(raw or "").strip())
    if text.startswith("+86"):
        text = text[3:]
    elif text.startswith("86") and len(text) == 13:
        text = text[2:]
    if not re.fullmatch(r"1[3-9]\d{9}", text):
        raise ValueError("手机号格式不对，需要 11 位中国大陆号码")
    return text


def normalize_code(raw):
    text = str(raw or "").strip()
    if not re.fullmatch(r"\d{6}", text):
        raise ValueError("验证码格式不对，需要 6 位数字")
    return text


def encode_component(raw):
    safe = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_.~"
    out = []
    for byte in raw:
        out.append(chr(byte) if byte in safe else "%%%02X" % byte)
    return "".join(out)


def escaped_path(path):
    clean = path if path.startswith("/") else "/" + path
    if len(clean) > 1 and clean.endswith("/"):
        clean = clean[:-1]
    return "/".join(encode_component(segment.encode("utf-8")) for segment in clean.split("/"))


def compact_json(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def signed_headers(method, path, body_string):
    content_md5 = base64.b64encode(hashlib.md5(body_string.encode("utf-8")).digest()).decode("ascii") \
        if body_string else ""
    date = formatdate(timeval=None, localtime=False, usegmt=True)
    nonce = str(uuid.uuid4())
    string_to_sign = "\n".join([
        method.upper(),
        escaped_path(path),
        "",
        content_md5,
        "application/json",
        date,
        nonce,
        "",
        "",
    ])
    signature = base64.b64encode(
        hmac.new(ACCESS_KEY_SECRET.encode("utf-8"), string_to_sign.encode("utf-8"),
                 hashlib.sha1).digest()).decode("ascii")
    headers = {
        "Authorization": "account %s:%s" % (ACCESS_KEY_ID, signature),
        "Date": date,
        "Nonce": nonce,
        "Content-Type": "application/json",
    }
    if content_md5:
        headers["Content-MD5"] = content_md5
    return headers


def make_base():
    return {
        "appid": APP_ID,
        "modelid": MODEL_ID,
        "version": CLIENT_VERSION,
        "devid": DEVICE_ID,
        "ua": CLIENT_UA,
        "traceid": os.urandom(16).hex(),
    }


def signed_post(path, body):
    body_string = compact_json(body)
    headers = signed_headers("POST", path, body_string)
    session = requests.Session()
    session.trust_env = False
    return session.post(BASE + path, headers=headers, data=body_string.encode("utf-8"),
                        timeout=20, verify=False)


def json_of(response):
    try:
        return response.json()
    except Exception:
        return {}


def first_text(*values):
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def send_code(phone):
    log("📤 发送短信验证码到 %s ..." % mask_phone(phone))
    body = {"base": make_base(), "param": {"ccode": "86", "phone": phone, "expire": 300}}
    response = signed_post(SEND_CODE_PATH, body)
    payload = json_of(response)
    if str(payload.get("code") or "") != SUCCESS_CODE:
        raise RuntimeError("发码失败: %s" % (first_text(payload.get("desc"), payload.get("message")) or payload.get("code")))
    data = payload.get("data") or {}
    msgid = first_text(data.get("msgid"), data.get("msgId"),
                       (data.get("data") or {}).get("msgid") if isinstance(data.get("data"), dict) else None,
                       (data.get("data") or {}).get("msgId") if isinstance(data.get("data"), dict) else None)
    if not msgid:
        raise RuntimeError("短信已发出，但接口没有返回 msgid")
    log("✅ 验证码已发送（有效期 300 秒）")
    return msgid


def login(phone, code, msgid):
    log("🔐 提交验证码登录 ...")
    body = {
        "base": make_base(),
        "param": {"ccode": "86", "phone": phone, "mcode": code, "msgid": msgid, "expire": 14 * 24 * 3600},
    }
    response = signed_post(LOGIN_PATH, body)
    payload = json_of(response)
    status = str(payload.get("code") or "")
    if status != SUCCESS_CODE:
        message = first_text(payload.get("desc"), payload.get("message")) or status
        raise RuntimeError("登录失败（code=%s）：%s" % (status, message))
    data = payload.get("data") or {}
    session_token = first_text(data.get("session"))
    if not session_token:
        raise RuntimeError("登录成功但响应缺少 session")
    return {
        "session": session_token,
        "userid": first_text(data.get("userid")),
    }


def verify_session(session_token):
    log("🔎 校验 session ...")
    headers = {"token": session_token, "Authorization": "Bearer %s" % session_token}
    try:
        session = requests.Session()
        session.trust_env = False
        response = session.get(INTEGRATION_BASE + TASKS_PATH, headers=headers, timeout=20, verify=False)
        payload = json_of(response)
        if str(payload.get("code") or "") == SUCCESS_CODE:
            log("✅ session 可用")
            return True
        log("⚠️ 校验未通过：%s" % (first_text(payload.get("desc"), payload.get("message")) or payload.get("code")))
    except Exception as error:
        log("⚠️ 校验异常：%s" % error)
    return False


def main():
    args = sys.argv[1:]
    do_verify = "--verify" in args
    note = ""
    if "--note" in args:
        try:
            note = args[args.index("--note") + 1]
        except Exception:
            note = ""
    positional = []
    skip_next = False
    for index, item in enumerate(args):
        if skip_next:
            skip_next = False
            continue
        if item == "--note":
            skip_next = True
            continue
        if item.startswith("--"):
            continue
        positional.append(item)

    phone = normalize_phone(positional[0]) if positional else ""
    code = positional[1] if len(positional) > 1 else ""

    print("╔══════════════════════════════════════════╗")
    print("║ 📱 Loomy 短信验证码登录                   ║")
    print("║ 手机号 → 验证码 → session                 ║")
    print("╚══════════════════════════════════════════╝")

    if not phone:
        phone = normalize_phone(input("📱 请输入手机号: ").strip())
    msgid = send_code(phone)
    if not code:
        code = normalize_code(input("📩 请输入收到的验证码: ").strip())
    else:
        code = normalize_code(code)

    result = login(phone, code, msgid)
    if do_verify:
        verify_session(result["session"])

    note = note or phone
    env_line = "%s|%s" % (note, result["session"])
    print("\n" + "-" * 50)
    print("✅ 将下面这行追加到 LOOMY_TOKENS")
    print("-" * 50)
    print(env_line)
    print("-" * 50)
    if result.get("userid"):
        print("userid: %s" % result["userid"])

    save_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "loomy_login_result.json")
    try:
        try:
            with open(save_file, encoding="utf-8") as handle:
                records = json.load(handle)
        except Exception:
            records = []
        records.append({"note": note, "phone": phone, "session": result["session"],
                        "userid": result.get("userid", ""), "at": time.strftime("%Y-%m-%d %H:%M:%S")})
        with open(save_file, "w", encoding="utf-8") as handle:
            json.dump(records, handle, ensure_ascii=False, indent=1)
        print("📁 结果已保存: %s" % save_file)
    except Exception as error:
        print("⚠️ 结果保存失败: %s" % error)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n已取消")
        sys.exit(130)
    except Exception as error:
        print("❌ %s" % error)
        sys.exit(1)
