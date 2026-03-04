-- Football Transfer Analysis - SQL Queries

-- 1. Kulüp başına oyuncu sayısı
SELECT c.club_name, COUNT(p.player_id) as oyuncu_sayisi
FROM clubs c
JOIN players p ON c.club_id = p.current_club_id
GROUP BY c.club_name
ORDER BY oyuncu_sayisi DESC
LIMIT 10;

-- 2. En çok gol atan 10 oyuncu
SELECT p.full_name, c.club_name, s.goals 
FROM players p, stats s, clubs c 
WHERE p.player_id = s.player_id AND p.current_club_id = c.club_id
ORDER BY s.goals DESC
LIMIT 10;

-- 3. Pozisyon başına ortalama pas yüzdesi
SELECT 
    SPLIT_PART(p.position, ',', 1) as ana_pozisyon,
    ROUND(AVG(s.pass_accuracy), 2) as ort_pas,
    COUNT(*) as oyuncu_sayisi
FROM players p
JOIN stats s ON p.player_id = s.player_id
WHERE s.pass_accuracy IS NOT NULL
AND s.appearances >= 10
GROUP BY SPLIT_PART(p.position, ',', 1)
ORDER BY ort_pas DESC;