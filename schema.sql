DROP TABLE IF EXISTS users;
CREATE TABLE users (
  id INTEGER PRIMARY KEY,
  username TEXT,
  password TEXT,
  monthlyBudget INTEGER,
  decimalPlaces INTEGER,
  displayCurrency TEXT,
  exchangeRate NUMERIC
);
CREATE UNIQUE INDEX udx_username ON users (username);
INSERT INTO users (username, password, monthlyBudget, decimalPlaces, displayCurrency, exchangeRate) VALUES ('will', '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8', 1000, 2, 'S$', 1);


DROP TABLE IF EXISTS entries;
CREATE TABLE entries (
  id INTEGER PRIMARY KEY,
  users_id INTEGER,
  date TEXT,
  monthcode INTEGER,
  daycode INTEGER,
  type INTEGER,
  amount NUMERIC
);


DROP TABLE IF EXISTS types;
CREATE TABLE types (
  id INTEGER PRIMARY KEY,
  users_id INTEGER,
  name TEXT
);
INSERT INTO types ( users_id, name ) VALUES
  (1, 'Food'), (1, 'Taxi'), (1, 'Others'), (1, 'Travel'), (1, 'Bills');
