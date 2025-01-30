import sqlite3
import csv
from collections import Counter
from difflib import SequenceMatcher  # Für die Ähnlichkeitsprüfung

# Funktion zur Berechnung der Ähnlichkeit zwischen zwei Strings
def calculate_similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()

# Funktion zur Konsolidierung der Nonagramme basierend auf Ähnlichkeit
def consolidate_nonagrams_with_similarity(nonagrams, threshold=0.8):
    consolidated = []
    seen = set()

    for nonagram, count in nonagrams:
        # Prüfe, ob das Nonagramm bereits konsolidiert wurde
        if any(calculate_similarity(nonagram, existing) > threshold for existing, _ in consolidated):
            continue
        consolidated.append((nonagram, count))
    
    return consolidated

# Schritt 1: SQLite-Datenbank erstellen und Tabelle für Wörter anlegen
conn = sqlite3.connect('nonagram_analysis.db')
cursor = conn.cursor()

# Tabelle für Wörter erstellen
cursor.execute('''
CREATE TABLE IF NOT EXISTS words (
    line_number INTEGER,
    position INTEGER,
    word TEXT
)
''')

# Schritt 2: CSV-Datei einlesen und Wörter in die Datenbank schreiben
with open('25-12-2024-mew.csv', 'r', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    line_number = 0
    for row in reader:
        line_number += 1
        # Template mit der neuen Reihenfolge erstellen
        combined_text = (
            f"<|System|>{row['system']}</s>"
            f"<|Benutzer|>{row['Benutzer']} "
            f", {row['Kontext']}</s>"
            f"<|Assistentin|> {row['Assistentin']}</s>"
        )
        words = combined_text.split()  # Zerlege den Text in Wörter
        for position, word in enumerate(words):
            cursor.execute('INSERT INTO words (line_number, position, word) VALUES (?, ?, ?)', 
                           (line_number, position, word))
    conn.commit()

# Schritt 3: Nonagramme in der SQL-Datenbank erstellen
# Erstelle eine temporäre Tabelle für Nonagramme
cursor.execute('''
CREATE TEMP TABLE nonagrams AS
SELECT 
    w1.line_number AS line_number,
    w1.word || '_' || w2.word || '_' || w3.word || '_' || w4.word || '_' || 
    w5.word || '_' || w6.word || '_' || w7.word || '_' || w8.word || '_' || w9.word AS nonagram
FROM words w1
JOIN words w2 ON w1.line_number = w2.line_number AND w1.position + 1 = w2.position
JOIN words w3 ON w1.line_number = w3.line_number AND w1.position + 2 = w3.position
JOIN words w4 ON w1.line_number = w4.line_number AND w1.position + 3 = w4.position
JOIN words w5 ON w1.line_number = w5.line_number AND w1.position + 4 = w5.position
JOIN words w6 ON w1.line_number = w6.line_number AND w1.position + 5 = w6.position
JOIN words w7 ON w1.line_number = w7.line_number AND w1.position + 6 = w7.position
JOIN words w8 ON w1.line_number = w8.line_number AND w1.position + 7 = w8.position
JOIN words w9 ON w1.line_number = w9.line_number AND w1.position + 8 = w9.position
''')

# Schritt 4: Häufigkeit der Nonagramme zählen und `_` hinzufügen, falls nötig
cursor.execute('''
CREATE TEMP TABLE nonagram_counts AS
SELECT 
    CASE 
        WHEN nonagram LIKE '<|System|>%' THEN nonagram
        ELSE '_' || nonagram
    END AS nonagram_with_prefix,
    COUNT(*) AS frequency
FROM nonagrams
GROUP BY nonagram_with_prefix
ORDER BY frequency DESC
''')

# Schritt 5: Hole die Nonagramme aus der Datenbank
cursor.execute('SELECT nonagram_with_prefix, frequency FROM nonagram_counts')
nonagrams = cursor.fetchall()

# Schritt 6: Konsolidierung der Nonagramme basierend auf Ähnlichkeit
consolidated_nonagrams = consolidate_nonagrams_with_similarity(nonagrams, threshold=0.8)

# Schritt 7: Ergebnisse im CSV-Format in eine Datei schreiben
output_file = 'haeufigste_nonagramme_mitte_konsolidiert.csv'
with open(output_file, 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    # Schreibe die Kopfzeile
    writer.writerow(["Nonagramm", "Häufigkeit"])
    # Schreibe die konsolidierten Nonagramme
    for nonagram, count in consolidated_nonagrams[:1000]:  # Top 1000 konsolidierte Nonagramme
        writer.writerow([nonagram, count])

# Verbindung schließen
conn.close()

print(f"Die 1000 häufigsten konsolidierten Nonagramme wurden im CSV-Format in der Datei '{output_file}' gespeichert.")
