import os
import requests
from bs4 import BeautifulSoup

# 安全地從 GitHub 密碼本讀取 WhatsApp 設定
WHATSAPP_PHONE = os.environ.get("WHATSAPP_PHONE")
WHATSAPP_APIKEY = os.environ.get("WHATSAPP_APIKEY")
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

def send_whatsapp_notification(site_name, title, url):
    if not WHATSAPP_PHONE or not WHATSAPP_APIKEY:
        print("[錯誤] 找不到 WhatsApp 設定檔")
        return
        
    # WhatsApp 的排版語法（* 代表粗體）
    text = f"🚨 *{site_name} 新貨/預訂上架！*\n\n*商品：*{title}\n\n👉 點我前往搶購：\n{url}"
    
    api_url = "https://api.callmebot.com/whatsapp.php"
    params = {
        "phone": WHATSAPP_PHONE,
        "text": text,
        "apikey": WHATSAPP_APIKEY
    }
    
    try:
        response = requests.get(api_url, params=params, timeout=10)
        if response.status_code == 200:
            print(f"[成功] 已發送 WhatsApp 通知：{title}")
        else:
            print(f"[失敗] WhatsApp API 錯誤，狀態碼：{response.status_code}")
    except Exception as e:
        print(f"[WhatsApp 錯誤] 無法發送通知: {e}")

def check_sites():
    notified_list = get_notified_list()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    for site in SITES:
        try:
            print(f"🔍 正在檢查: {site['name']}...")
            response = requests.get(site["url"], headers=headers, timeout=15)
            
            if response.status_code != 200:
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
                        send_whatsapp_notification(site['name'], title, link)
                        save_to_history(unique_id)
        except Exception as e:
            print(f"  [錯誤] 檢查 {site['name']} 發生異常: {e}")

if __name__ == "__main__":
    print("啟動單次掃描...")
    check_sites()
    print("掃描完成。")
