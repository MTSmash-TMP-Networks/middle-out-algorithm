import sqlite3
import csv
from collections import Counter

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
            f"<System>{row['system']}</s>"
            f"<Benutzer>{row['Benutzer']} "
            f", {row['Kontext']}</s>"
            f"<Assistentin> {row['Assistentin']}</s>"
        )
        words = combined_text.split()  # Zerlege den Text in Wörter
        for position, word in enumerate(words):
            cursor.execute('INSERT INTO words (line_number, position, word) VALUES (?, ?, ?)', 
                           (line_number, position, word))
    conn.commit()

# Schritt 3: Nonagramme von der Mitte nach außen erstellen
cursor.execute('SELECT line_number, position, word FROM words ORDER BY line_number, position')
rows = cursor.fetchall()

# Nonagramme zählen
nonagram_counter = Counter()
for i in range(len(rows) - 8):  # -8, da wir 9 Wörter benötigen
    # Prüfe, ob genügend Wörter in derselben Zeile vorhanden sind
    if all(rows[i][0] == rows[i+j][0] for j in range(9)):  # Prüfe, ob alle Wörter in derselben Zeile sind
        # Wähle Wörter von der Mitte nach außen
        middle_index = i + 4  # Das mittlere Wort (Index 4 im Nonagramm)
        nonagram = [rows[middle_index][2]]  # Beginne mit dem mittleren Wort
        for offset in range(1, 5):  # Gehe abwechselnd nach links und rechts
            nonagram.insert(0, rows[middle_index - offset][2])  # Füge ein Wort links hinzu
            nonagram.append(rows[middle_index + offset][2])  # Füge ein Wort rechts hinzu
        nonagram_counter["_".join(nonagram)] += 1

# Schritt 4: Ergebnisse im CSV-Format in eine Datei schreiben
output_file = 'haeufigste_nonagramme_mitte.csv'
with open(output_file, 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    # Schreibe die Kopfzeile
    writer.writerow(["Nonagramm", "Nummer"])
    index = 1  # Start der Nummerierung
    # Nur die 1000 häufigsten Nonagramme ausgeben
    for nonagram, count in nonagram_counter.most_common(1000):  # Top 1000 Nonagramme
        # Prüfe, ob das Nonagramm mit "Links" beginnt
        if not nonagram.startswith("Links"):
            nonagram = f"_{nonagram}"  # Füge "_" am Anfang hinzu
        writer.writerow([nonagram, index])  # Schreibe Nonagramm und Nummer
        index += 1  # Erhöhe die Nummerierung

# Verbindung schließen
conn.close()

print(f"Die 1000 häufigsten Nonagramme (von der Mitte nach außen) wurden im CSV-Format in der Datei '{output_file}' gespeichert.")
