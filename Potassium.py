import time
import requests
from bs4 import BeautifulSoup

TARGET_URL = "https://weao.xyz"
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1547891715279687763/jGm9yeR8j_k5kOHFS-Knmt57n8bm8vTSTiiAVJAlmywH0HsSEeCjNL-2XRkOqHrU6flW"

last_status = None

def check_potassium_status():
    global last_status
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(TARGET_URL, headers=headers)
        
        if response.status_code != 200:
            print(f"[!] 웹사이트 접속 실패: {response.status_code}")
            return

        soup = BeautifulSoup(response.text, 'html.parser')
        
        potassium_element = None
        for tag in soup.find_all(text=lambda t: t and 'Potassium' in t):
            potassium_element = tag.parent
            break
            
        if not potassium_element:
            print("[!] Potassium 항목을 찾지 못했습니다.")
            return

        element_html = str(potassium_element)
        
        current_status = "Unknown"
        if "green" in element_html or "🟢" in element_html or "working" in element_html.lower():
            current_status = "Online (작동 중)"
        else:
            current_status = "Offline (막힘/점검중)"

        print(f"[*] 현재 포타슘 상태: {current_status}")

        if last_status is not None and last_status != current_status:
            discord_payload = {
                "content": f"🚨 **포타슘(Potassium) 상태 변경 감지!**\n상태: `{current_status}`"
            }
            requests.post(DISCORD_WEBHOOK_URL, json=discord_payload)
            print("[!] 디스코드 알림 전송 완료!")

        last_status = current_status

    except Exception as e:
        print(f"[!] 에러 발생: {e}")

if __name__ == "__main__":
    print("[*] 포타슘 상태 감지 봇 시작...")
    while True:
        check_potassium_status()
        time.sleep(60)
