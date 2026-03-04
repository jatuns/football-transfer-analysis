import pandas as pd
import psycopg2

# Veritabanı bağlantısı
conn = psycopg2.connect(
    host="localhost",
    database="football_transfers",
    user="postgres",
    password="CXL3pCbw0eLBwPb"
)
cursor = conn.cursor()

# CSV'yi oku
df = pd.read_csv("data/raw/players_data-2024_2025.csv")

# Tekrar kolonları temizle
tekrar_kolonlar = [col for col in df.columns if any(
    col.startswith(prefix) for prefix in [
        'Rk_stats_', 'Nation_stats_', 'Age_stats_', 
        'Pos_stats_', 'Comp_stats_', 'Born_stats_'
    ]
)]
df = df.drop(columns=tekrar_kolonlar)

# Her çalıştırmada temiz başla
cursor.execute("TRUNCATE TABLE keeper_stats, stats, transfers, players, clubs, leagues RESTART IDENTITY CASCADE")
conn.commit()
print("🧹 Tablolar temizlendi!")

# ADIM 1: Ligleri ekle
lig_ulke = {
    'eng Premier League': 'England',
    'es La Liga': 'Spain',
    'it Serie A': 'Italy',
    'fr Ligue 1': 'France',
    'de Bundesliga': 'Germany'
}

lig_kulup = {
    'eng Premier League': 20,
    'es La Liga': 20,
    'it Serie A': 20,
    'fr Ligue 1': 18,
    'de Bundesliga': 18
}

for lig, ulke in lig_ulke.items():
    cursor.execute("""
        INSERT INTO leagues (league_name, country, num_clubs)
        VALUES (%s, %s, %s)
        ON CONFLICT DO NOTHING
    """, (lig, ulke, lig_kulup[lig]))

conn.commit()
print("✅ Ligler eklendi!")

cursor.execute("SELECT * FROM leagues")
print(cursor.fetchall())



# ADIM 2: Kulüpleri ekle
# Önce league_id'leri çek
cursor.execute("SELECT league_id, league_name FROM leagues")
lig_map = {row[1]: row[0] for row in cursor.fetchall()}

kulupler = df[['Squad', 'Comp']].drop_duplicates()

for _, row in kulupler.iterrows():
    league_id = lig_map.get(row['Comp'])
    cursor.execute("""
        INSERT INTO clubs (club_name, league_id)
        VALUES (%s, %s)
        ON CONFLICT DO NOTHING
    """, (row['Squad'], league_id))

conn.commit()
print("✅ Kulüpler eklendi!")

cursor.execute("SELECT COUNT(*) FROM clubs")
print(f"Toplam kulüp sayısı: {cursor.fetchone()[0]}")


# ADIM 3: Oyuncuları ekle
# Önce club_id'leri çek
cursor.execute("SELECT club_id, club_name FROM clubs")
kulup_map = {row[1]: row[0] for row in cursor.fetchall()}

oyuncular = df[['Player', 'Nation', 'Pos', 'Age', 'Born', 'Squad']].drop_duplicates(subset=['Player', 'Squad'])

for _, row in oyuncular.iterrows():
    club_id = kulup_map.get(row['Squad'])
    nation = str(row['Nation']).split(' ')[-1] if pd.notna(row['Nation']) else None
    age = int(row['Age']) if pd.notna(row['Age']) else None
    
    cursor.execute("""
        INSERT INTO players (full_name, nationality, position, current_club_id)
        VALUES (%s, %s, %s, %s)
    """, (row['Player'], nation, row['Pos'], club_id))

conn.commit()
print("✅ Oyuncular eklendi!")

cursor.execute("SELECT COUNT(*) FROM players")
print(f"Toplam oyuncu sayısı: {cursor.fetchone()[0]}")

# ADIM 4: Saha oyuncusu istatistiklerini ekle
cursor.execute("SELECT player_id, full_name, current_club_id FROM players")
oyuncu_map = {(row[1], row[2]): row[0] for row in cursor.fetchall()}

outfield = df[df['Pos'] != 'GK'].copy()

basari = 0
hata = 0

for _, row in outfield.iterrows():
    club_id = kulup_map.get(row['Squad'])
    player_id = oyuncu_map.get((row['Player'], club_id))
    
    if not player_id:
        hata += 1
        continue

    cursor.execute("""
        INSERT INTO stats (
            player_id, club_id, season, appearances, minutes_played,
            goals, assists, key_passes, progressive_passes, progressive_carries,
            duels_won, duels_total, pass_accuracy, shots_on_target,
            yellow_cards, red_cards, xG, xA
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        player_id, club_id, '2024/25',
        row.get('MP'), row.get('Min'),
        row.get('Gls'), row.get('Ast'),
        row.get('KP'), row.get('PrgP'),
        row.get('PrgC'), row.get('Won'),
        row.get('Won'), row.get('Cmp%'),
        row.get('SoT'), row.get('CrdY'),
        row.get('CrdR'), row.get('xG'),
        row.get('xA')
    ))
    basari += 1

conn.commit()
print(f"✅ Saha oyuncusu istatistikleri eklendi! {basari} başarılı, {hata} hatalı")

# ADIM 5: Kaleci istatistiklerini ekle
gk = df[df['Pos'] == 'GK'].copy()

basari = 0
hata = 0

for _, row in gk.iterrows():
    club_id = kulup_map.get(row['Squad'])
    player_id = oyuncu_map.get((row['Player'], club_id))
    
    if not player_id:
        hata += 1
        continue

    cursor.execute("""
        INSERT INTO keeper_stats (
            player_id, club_id, season, mp, minutes_played,
            ga, ga90, sota, saves, save_pct,
            cs, cs_pct, pksv, psxg, psxg_pm
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        player_id, club_id, '2024/25',
        row.get('MP'), row.get('Min'),
        row.get('GA'), row.get('GA90'),
        row.get('SoTA'), row.get('Saves'),
        row.get('Save%'), row.get('CS'),
        row.get('CS%'), row.get('PKsv'),
        row.get('PSxG'), row.get('PSxG+/-')
    ))
    basari += 1

conn.commit()
print(f"✅ Kaleci istatistikleri eklendi! {basari} başarılı, {hata} hatalı")

# ADIM 6: Transfer verilerini yükle
import re

transfers_df = pd.read_csv("data/raw/transfers_2024_25.csv")

def parse_fee(fee_str):
    if pd.isna(fee_str):
        return None
    fee_str = str(fee_str).strip()
    
    # Loan fee durumu
    if "Loan fee:" in fee_str:
        fee_str = fee_str.replace("Loan fee:", "").strip()
    
    fee_str = fee_str.replace("€", "").strip()
    
    try:
        if "m" in fee_str:
            return float(fee_str.replace("m", "")) * 1_000_000
        if "k" in fee_str:
            return float(fee_str.replace("k", "")) * 1_000
        return float(fee_str)
    except:
        return None

transfers_df["fee_numeric"] = transfers_df["transfer_fee"].apply(parse_fee)

basari = 0
hata = 0

for _, row in transfers_df.iterrows():
    # Oyuncuyu bul
    cursor.execute("SELECT player_id FROM players WHERE full_name = %s LIMIT 1", (row["player"],))
    player = cursor.fetchone()
    
    # from_club'ı bul
    cursor.execute("SELECT club_id FROM clubs WHERE club_name ILIKE %s LIMIT 1", (f"%{row['from_club']}%",))
    from_club = cursor.fetchone()
    
    # to_club'ı bul
    cursor.execute("SELECT club_id FROM clubs WHERE club_name ILIKE %s LIMIT 1", (f"%{row['to_club']}%",))
    to_club = cursor.fetchone()
    
    if not player:
        hata += 1
        continue
    
    cursor.execute("""
        INSERT INTO transfers (player_id, from_club_id, to_club_id, transfer_fee, transfer_type)
        VALUES (%s, %s, %s, %s, %s)
    """, (
        player[0],
        from_club[0] if from_club else None,
        to_club[0] if to_club else None,
        row["fee_numeric"],
        row["window"]
    ))
    basari += 1

conn.commit()
print(f"✅ Transferler yüklendi! {basari} başarılı, {hata} eşleşmeyen")

conn.close()