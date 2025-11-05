-- CREATE DATABASE IF NOT EXISTS Football;

USE football;

CREATE TABLE IF NOT EXISTS League (
    league_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    UNIQUE (name)
);

CREATE TABLE IF NOT EXISTS Season (
    season_id INT AUTO_INCREMENT PRIMARY KEY,
    label VARCHAR(9) NOT NULL,
    start_year SMALLINT NOT NULL,
    end_year SMALLINT NOT NULL,
    UNIQUE (label)
);

CREATE TABLE IF NOT EXISTS Team (
    team_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    UNIQUE (name)
);

CREATE TABLE IF NOT EXISTS League_Season (
    ls_id INT AUTO_INCREMENT PRIMARY KEY,
    league_id INT NOT NULL,
    season_id INT NOT NULL,
    FOREIGN KEY (league_id) REFERENCES League(league_id),
    FOREIGN KEY (season_id) REFERENCES Season(season_id),
    UNIQUE (league_id, season_id)
);

CREATE TABLE IF NOT EXISTS Metric (
    metric_id INT AUTO_INCREMENT PRIMARY KEY,
    ls_id INT NOT NULL,
    team_id INT NOT NULL,

    -- Statistics
    games_played       SMALLINT,
    players_used       SMALLINT,
    avg_age            DECIMAL(4,2),
    possession         DECIMAL(5,2),
    goals              SMALLINT,
    assists            SMALLINT,
    pens_made          SMALLINT,
    pens_attempted     SMALLINT,
    cards_yellow       SMALLINT,
    cards_red          SMALLINT,
    fouls              SMALLINT,
    fouled             SMALLINT,
    offsides           SMALLINT,
    crosses            SMALLINT,
    interceptions      SMALLINT,
    tackles_won        SMALLINT,
    pens_won           SMALLINT,
    pens_conceded      SMALLINT,
    own_goals          SMALLINT,

    xg                 DECIMAL(7,3),
    npxg               DECIMAL(7,3),
    xg_assist          DECIMAL(7,3),
    progressive_passes INT,
    progressive_carries INT,
    ball_recoveries    INT,
    aerials_won        INT,
    aerials_lost       INT,

    FOREIGN KEY (ls_id) REFERENCES League_Season(ls_id),
    FOREIGN KEY (team_id) REFERENCES Team(team_id),
    UNIQUE(ls_id, team_id) 
);

-- Index creation to speed up lookup
CREATE INDEX IDX_ls_league ON League_Season(league_id);
CREATE INDEX IDX_ls_season ON League_Season(season_id);
CREATE INDEX IDX_metric_ls ON Metric(ls_id);
CREATE INDEX IDX_metric_team ON Metric(team_id);