DROP TABLE IF EXISTS entries;
CREATE TABLE entries (
  id INTEGER PRIMARY KEY,
  date TEXT,
  monthcode INTEGER,
  daycode INTEGER,
  type INTEGER,
  amount NUMERIC
);

DROP TABLE IF EXISTS types;
CREATE TABLE types (
  id INTEGER PRIMARY KEY,
  name TEXT
);

INSERT INTO types ( name ) VALUES
  ('Food'), ('Taxi'), ('Others'), ('Bills');

DROP TABLE IF EXISTS settings;
CREATE TABLE settings (
  monthlyBudget INTEGER,
  decimalPlaces INTEGER,
  displayCurrency TEXT,
  exchangeRate NUMERIC
);
INSERT INTO settings ( monthlyBudget, decimalPlaces, displayCurrency, exchangeRate ) VALUES ( 1000, 2, 'S$', 1);
