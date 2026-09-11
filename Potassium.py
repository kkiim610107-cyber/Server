import os
import time
import threading
import requests
from bs4 import BeautifulSoup
from flask import Flask

app = Flask(__name__)

# 설정
TARGET_URL = "https://weao.xyz"
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1547891715279687763/jGm9yeR8j_k5kOHFS-Knmt57n8bm8vTSTiiAVJAlmywH0HsSEeCjNL-2XRkOqHrU6flW"

last_status = None

def monitor_potassium():
    global last_status
    while True:
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(TARGET_URL, headers=headers)
            
            if response.status_code != 200:
                print(f"[!] 웹사이트 접속 실패: {response.status_code}")
                time.sleep(60)
                continue

            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 최신 방식(string)으로 변경하여 경고 해결
            potassium_element = None
            for tag in soup.find_all(string=lambda t: t and 'Potassium' in t):
                potassium_element = tag.parent
                break
                
            if not potassium_element:
                print("[!] Potassium 항목을 찾지 못했습니다.")
                time.sleep(60)
                continue

            element_html = str(potassium_element)
            
            current_status = "Unknown"
            if "green" in element_html or "🟢" in element_html or "working" in element_html.lower():
                current_status = "Online (작동 중)"
            else:
                current_status = "Offline (막힘/점검중)"

            print(f"[*] 현재 포타슘 상태: {current_stats if 'current_stats' in locals() else current_status}")

            if last_status is not None and last_status != current_status:
                discord_payload = {
                    "content": f"🚨 **포타슘(Potassium) 상태 변경 감지!**\n상태: `{current_status}`"
                }
                requests.post(DISCORD_WEBHOOK_URL, json=discord_payload)
                print("[!] 디스코드 알림 전송 완료!")

            last_status = current_status

        except Exception as e:
            print(f"[!] 에러 발생: {e}")
            
        time.sleep(60)  # 60초마다 체크

@app.route('/')
def home():
    return "Potassium Monitor Bot is Running!"

if __name__ == "__main__":
    # 백그라운드에서 감시 스레드 실행
    t = threading.Thread(target=monitor_potassium)
    t.daemon = True
    t.start()
    
    # 렌더가 지정해 주는 포트를 필수로 바인딩해야 에러가 안 납니다!
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
