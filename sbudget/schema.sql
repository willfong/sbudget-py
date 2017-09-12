CREATE TABLE entries (
  id INTEGER PRIMARY KEY,
  date TEXT,
  monthcode INTEGER,
  daycode INTEGER,
  type INTEGER,
  amount NUMERIC
);

CREATE TABLE types (
  id INTEGER PRIMARY KEY,
  name TEXT
);

INSERT INTO types ( name ) VALUES
  ('Food'), ('Bills'), ('Others');

CREATE TABLE settings (
  monthlyBudget INTEGER,
  decimalPlaces INTEGER,
  displayCurrency TEXT
);
INSERT INTO settings ( monthlyBudget, decimalPlaces, displayCurrency ) VALUES ( 1000, 2, 'S$');
