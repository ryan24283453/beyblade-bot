import os
import time
import threading
import requests
from bs4 import BeautifulSoup
from flask import Flask  # 新增網頁套件

# ==================== Flask 網頁伺服器設定 ====================
app = Flask(__name__)

@app.route('/')
def home():
    # 當有人（或 UptimeRobot）訪問網址時，會顯示這行字，確保程式沒休眠
    return "🤖 陀螺監控機器人運作中！"

# ==================== 核心設定 ====================
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1527016875194843297/aNNnXUHaqO3hnKRVZGoLnSkcFlbZPjBpJQ2RIhQg79hGGX4GSPHZfdFwr29nWoap1pR4"
CHECK_INTERVAL = 120  # 每 2 分鐘檢查一次
HISTORY_FILE = "hk_beyblade_history.txt"

KEYWORDS = ["預購", "預約", "預訂", "BX", "UX", "Beyblade", "戰鬥陀螺"]

SITES = [
    {
        "name": "玩具反斗城 (Toys R Us HK)",
        "url": "https://www.toysrus.com.hk/zh-hk/toys/action-figures-playsets/beyblade/", 
        "domain": "https://www.toysrus.com.hk",
        "card_selector": "div.product-item",
        "title_selector": "a.name",
        "link_selector": "a.name"
    },
    {
        "name": "玩具站 (T-Club)",
        "url": "https://www.tclub.com.hk/categories/beyblade", 
        "domain": "https://www.tclub.com.hk",
        "card_selector": "div.product-item",
        "title_selector": "div.title a",
        "link_selector": "div.title a"
    },
    {
        "name": "孤注一扭",
        "url": "https://www.gozoo.com.hk/categories/beyblade", 
        "domain": "", 
        "card_selector": "li.box-item",
        "title_selector": "div.title",
        "link_selector": "a"
    }
]

def get_notified_list():
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        return f.read().splitlines()

def save_to_history(item_name):
    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(item_name + "\n")

def send_discord_notification(site_name, title, url):
    payload = {
        "username": "香港陀螺預購情報員",
        "avatar_url": "https://i.imgur.com/X4uN0mG.png", 
        "embeds": [{
            "title": f"🚨 {site_name} 新貨/預訂上架！",
            "description": f"**商品：** {title}\n\n[👉 點我立刻前往搶購]({url})",
            "color": 5814783,
            "footer": {"text": "香港玩具店即時監控系統"}
        }]
    }
    try:
        requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=10)
    except Exception as e:
        print(f"[Discord 錯誤] 無法發送通知: {e}")

def check_sites():
    notified_list = get_notified_list()
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    for site in SITES:
        try:
            print(f"🔍 正在檢查: {site['name']}...")
            response = requests.get(site["url"], headers=headers, timeout=15)
            
            if response.status_code != 200:
                print(f"  [警告] {site['name']} 讀取失敗，狀態碼：{response.status_code}")
                continue
                
            soup = BeautifulSoup(response.text, 'html.parser')
            products = soup.select(site["card_selector"])

            for product in products:
                title_tag = product.select_one(site["title_selector"])
                link_tag = product.select_one(site["link_selector"])
                
                if not title_tag or not link_tag:
                    continue
                    
                title = title_tag.text.strip()
                link = link_tag.get('href', '')
                
                if not link.startswith("http"):
                    link = site["domain"] + link

                if any(kw.upper() in title.upper() for kw in KEYWORDS):
                    unique_id = f"[{site['name']}] {title}"
                    if unique_id not in notified_list:
                        print(f"  ✨ [發現新商品] {title}")
                        send_discord_notification(site['name'], title, link)
                        save_to_history(unique_id)
                        
        except Exception as e:
            print(f"  [錯誤] 檢查 {site['name']} 時發生異常: {e}")

# 背景監控執行緒
def run_monitor_loop():
    print("🤖 背景陀螺預購監控執行緒已啟動...")
    while True:
        check_sites()
        print(f"💤 休息 {CHECK_INTERVAL} 秒後繼續...")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    # 啟動背景監控執行緒
    monitor_thread = threading.Thread(target=run_monitor_loop, daemon=True)
    monitor_thread.start()
    
    # 啟動 Flask 網頁伺服器（Render 會自動偵測 PORT）
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)