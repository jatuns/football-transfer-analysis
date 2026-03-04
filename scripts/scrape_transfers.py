from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd
import time

options = webdriver.ChromeOptions()
options.add_argument("--no-sandbox")
options.add_argument("--window-size=1920,1080")
options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

big5 = {"England", "Spain", "Germany", "Italy", "France"}

def get_country(td):
    img = td.find("img")
    if img and img.get("title"):
        return img["title"]
    return ""

def scrape_window(saison_id, transferfenster, pencere_adi):
    transfers = []
    for page in range(1, 11):
        print(f"{pencere_adi} — Sayfa {page} çekiliyor...")
        url = f"https://www.transfermarkt.com/statistik/transferrekorde/statistik/top/plus/0/galerie/0?saison_id={saison_id}&transferfenster={transferfenster}&land_id=&ausrichtung=&spielerposition_id=&altersklasse=&leihe=&w_s=&plus=1&page={page}"
        driver.get(url)
        time.sleep(3)
        
        soup = BeautifulSoup(driver.page_source, "lxml")
        table = soup.find("table", class_="items")
        if not table:
            continue
        
        rows = table.find("tbody").find_all("tr")
        
        for row in rows:
            tds = row.find_all("td")
            if len(tds) < 12:
                continue
            
            try:
                player   = tds[3].get_text(strip=True)
                position = tds[4].get_text(strip=True)
                season   = tds[5].get_text(strip=True)
                to_club  = tds[9].get_text(strip=True)
                to_league = tds[10].get_text(strip=True)
                fee      = tds[11].get_text(strip=True)
                
                # from_club td[6] veya td[7]'den
                from_text = tds[7].get_text(strip=True)
                from_country = get_country(tds[6])
                to_country   = get_country(tds[8])
                
                if not player:
                    continue
                    
                if from_country in big5 or to_country in big5:
                    transfers.append({
                        "player": player,
                        "position": position,
                        "season": season,
                        "from_club": from_text,
                        "from_country": from_country,
                        "to_club": to_club,
                        "to_league": to_league,
                        "to_country": to_country,
                        "transfer_fee": fee,
                        "window": pencere_adi
                    })
            except Exception as e:
                continue
    
    return transfers

transfers = scrape_window("2024", "sommer", "Yaz 2024")
transfers += scrape_window("2024", "winter", "Ocak 2025")

df = pd.DataFrame(transfers)
print(f"\nToplam {len(df)} transfer bulundu!")
print(df.head(10))

df.to_csv("data/raw/transfers_2024_25.csv", index=False)
print("✅ CSV kaydedildi!")

driver.quit()