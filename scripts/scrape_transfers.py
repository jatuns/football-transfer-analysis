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

def get_img_title(td, index=0):
    imgs = td.find_all("img")
    return imgs[index]["title"] if len(imgs) > index else ""

def scrape_window(w_s, pencere_adi):
    transfers = []
    for page in range(1, 11):
        print(f"{pencere_adi} — Sayfa {page} çekiliyor...")
        url = f"https://www.transfermarkt.com/transfers/transferrekorde/statistik/top/plus/1/galerie/0?saison_id=2024&land_id=&ausrichtung=&spielerposition_id=&altersklasse=&jahrgang=0&leihe=&w_s={w_s}&page={page}"
        driver.get(url)
        time.sleep(3)

        soup = BeautifulSoup(driver.page_source, "lxml")
        table = soup.find("table", class_="items")
        if not table:
            continue

        rows = table.find("tbody").find_all("tr")

        for row in rows:
            tds = row.find_all("td")
            if len(tds) < 18:
                continue
            try:
                player       = tds[3].get_text(strip=True)
                position     = tds[4].get_text(strip=True)
                age          = tds[5].get_text(strip=True)
                market_value = tds[6].get_text(strip=True)
                season       = tds[7].get_text(strip=True)
                from_club    = tds[11].get_text(strip=True)
                from_league  = tds[12].get_text(strip=True)
                from_country = get_img_title(tds[12])
                to_club      = tds[15].get_text(strip=True)
                to_league    = tds[16].get_text(strip=True)
                to_country   = get_img_title(tds[16])
                fee          = tds[17].get_text(strip=True)

                if not player:
                    continue

                if from_country in big5 or to_country in big5:
                    transfers.append({
                        "player":       player,
                        "position":     position,
                        "age":          age,
                        "market_value": market_value,
                        "season":       season,
                        "from_club":    from_club,
                        "from_league":  from_league,
                        "from_country": from_country,
                        "to_club":      to_club,
                        "to_league":    to_league,
                        "to_country":   to_country,
                        "transfer_fee": fee,
                        "window":       pencere_adi
                    })
            except Exception:
                continue

    return transfers

transfers  = scrape_window("s", "Yaz 2024")
transfers += scrape_window("w", "Ocak 2025")

df = pd.DataFrame(transfers)
print(f"\nToplam {len(df)} transfer bulundu!")
print(df[["player", "from_club", "from_country", "to_club", "to_country", "transfer_fee"]].head(10))

df.to_csv("data/raw/transfers_2024_25.csv", index=False)
print("✅ CSV kaydedildi!")

driver.quit()