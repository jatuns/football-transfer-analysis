-- Football Transfer Analysis
-- Database Schema

CREATE TABLE leagues (
    league_id SERIAL PRIMARY KEY,
    league_name VARCHAR(100) NOT NULL,
    country VARCHAR(100) NOT NULL,
    num_clubs INT
);

CREATE TABLE clubs (
    club_id SERIAL PRIMARY KEY,
    club_name VARCHAR(100) NOT NULL,
    league_id INT REFERENCES leagues(league_id),
    city VARCHAR(100),
    founded_year INT
);

CREATE TABLE players (
    player_id SERIAL PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    nationality VARCHAR(100),
    birth_date DATE,
    position VARCHAR(50),
    current_club_id INT REFERENCES clubs(club_id)
);

CREATE TABLE stats (
    stat_id SERIAL PRIMARY KEY,
    player_id INT REFERENCES players(player_id),
    club_id INT REFERENCES clubs(club_id),
    season VARCHAR(10),
    appearances INT,
    minutes_played INT,
    goals INT,
    assists INT,
    key_passes INT,
    progressive_passes INT,
    progressive_carries INT,
    duels_won INT,
    duels_total INT,
    pass_accuracy DECIMAL(5,2),
    shots_on_target INT,
    yellow_cards INT,
    red_cards INT,
    xG DECIMAL(5,2),
    xA DECIMAL(5,2)
);

CREATE TABLE keeper_stats (
    keeper_stat_id SERIAL PRIMARY KEY,
    player_id INT REFERENCES players(player_id),
    club_id INT REFERENCES clubs(club_id),
    season VARCHAR(10),
    mp INT,
    minutes_played INT,
    ga DECIMAL(5,2),
    ga90 DECIMAL(5,2),
    sota INT,
    saves INT,
    save_pct DECIMAL(5,2),
    cs INT,
    cs_pct DECIMAL(5,2),
    pksv INT,
    psxg DECIMAL(5,2),
    psxg_pm DECIMAL(5,2)
);

CREATE TABLE transfers (
    transfer_id SERIAL PRIMARY KEY,
    player_id INT REFERENCES players(player_id),
    from_club_id INT REFERENCES clubs(club_id),
    to_club_id INT REFERENCES clubs(club_id),
    transfer_fee DECIMAL(15,2),
    transfer_date DATE,
    transfer_type VARCHAR(50)
);