import sqlite3
import csv
from collections import Counter

# Schritt 1: SQLite-Datenbank erstellen und Tabelle für Wörter anlegen
conn = sqlite3.connect('quadrigram_analysis.db')
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

# Schritt 3: Quadrigramme aus der Datenbank erstellen
cursor.execute('SELECT line_number, position, word FROM words ORDER BY line_number, position')
rows = cursor.fetchall()

# Quadrigramme zählen
quadrigram_counter = Counter()
for i in range(len(rows) - 3):  # -3, da wir 4 Wörter benötigen
    # Hole das aktuelle Wort und die nächsten drei Wörter
    if rows[i][0] == rows[i+1][0] == rows[i+2][0] == rows[i+3][0]:  # Prüfe, ob sie in derselben Zeile sind
        quadrigram = f"{rows[i][2]}_{rows[i+1][2]}_{rows[i+2][2]}_{rows[i+3][2]}"
        quadrigram_counter[quadrigram] += 1

# Schritt 4: Ergebnisse im CSV-Format in eine Datei schreiben
output_file = 'haeufigste_quadrigramme.csv'
with open(output_file, 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    # Schreibe die Kopfzeile
    writer.writerow(["Quadrigramm", "Nummer"])
    index = 1  # Start der Nummerierung
    # Nur die 1000 häufigsten Quadrigramme ausgeben
    for quadrigram, count in quadrigram_counter.most_common(1000):  # Top 1000 Quadrigramme
        # Prüfe, ob das Quadrigramm mit "Links" beginnt
        if not quadrigram.startswith("Links"):
            quadrigram = f"_{quadrigram}"  # Füge "_" am Anfang hinzu
        writer.writerow([quadrigram, index])  # Schreibe Quadrigramm und Nummer
        index += 1  # Erhöhe die Nummerierung

# Verbindung schließen
conn.close()

print(f"Die 1000 häufigsten Quadrigramme wurden im CSV-Format in der Datei '{output_file}' gespeichert.")
