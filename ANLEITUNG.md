# Anleitung zum Projekt – Stand Meilenstein 1

*Für alle, die das Projekt noch nie gesehen haben. Von vorne bis hinten lesen
dauert etwa 45 Minuten. Danach weißt du, worum es geht, wie man alles startet,
was die Bilder zeigen und was du im Meilenstein-Gespräch sagen kannst.*

**Inhalt**

1. [Das Projekt in einer Minute](#1-das-projekt-in-einer-minute)
2. [Grundbegriffe – ganz einfach erklärt](#2-grundbegriffe--ganz-einfach-erklärt)
3. [Die Daten: Was steht in den Dateien?](#3-die-daten-was-steht-in-den-dateien)
4. [Rundgang durch den Ordner](#4-rundgang-durch-den-ordner)
5. [Bedienung Schritt für Schritt](#5-bedienung-schritt-für-schritt)
6. [Was wir gemacht haben – der rote Faden](#6-was-wir-gemacht-haben--der-rote-faden)
7. [Die Erkenntnisse – Bild für Bild](#7-die-erkenntnisse--bild-für-bild)
8. [Die Baseline – Ergebnisse verstehen](#8-die-baseline--ergebnisse-verstehen)
9. [Warum haben wir das so gemacht? (Entscheidungen)](#9-warum-haben-wir-das-so-gemacht-entscheidungen)
10. [Grenzen und offene Punkte](#10-grenzen-und-offene-punkte)
11. [Wie geht es weiter? (Meilenstein 2)](#11-wie-geht-es-weiter-meilenstein-2)
12. [Spickzettel: die wichtigsten Zahlen](#12-spickzettel-die-wichtigsten-zahlen)
13. [Vorschlag für die Meilenstein-Präsentation](#13-vorschlag-für-die-meilenstein-präsentation)
14. [Fragen, die kommen können – mit Antworten](#14-fragen-die-kommen-können--mit-antworten)

---

## 1. Das Projekt in einer Minute

Ein Satellit (**EO-1 mit dem Sensor Hyperion**) hat Felder fotografiert, aber nicht wie
eine normale Kamera mit 3 Farben (Rot, Grün, Blau), sondern mit **über 200 „Farben“**
(Wellenlängen), auch solchen, die das Auge nicht sieht (Infrarot). Für jeden Bildpunkt
(30 × 30 m Feld) haben wir also eine Kurve: *wie viel Licht wird bei welcher Wellenlänge
zurückgeworfen?* Diese Kurve heißt **Spektrum**.

**Die Aufgabe:** Ein Computerprogramm soll allein aus diesem Spektrum (plus Region und
Monat) erkennen,

1. **welche Pflanze** auf dem Feld wächst (**Crop**: Mais, Sojabohne, Winterweizen,
   Baumwolle, Reis) **und**
2. **in welchem Wachstumsstadium** sie ist (**Stage**: vom Auflaufen bis zur Ernte, 6 Stufen).

Das ist „hierarchisch“, weil das Stadium zur Pflanze gehört: Es gibt z. B. Reis nur in
zwei der sechs Stadien.

**Wozu?** Wer weiß, was wo wächst und wie weit es ist, kann Ernten vorhersagen,
Bewässerung und Düngung planen, Versicherungsschäden prüfen oder Förderanträge
kontrollieren – für riesige Flächen, ohne hinzufahren.

**Was wir in Meilenstein 1 gemacht haben:**

* die Daten gründlich untersucht (**EDA** = explorative Datenanalyse),
* sie bereinigt (**Pre-Processing**),
* ein erstes, einfaches Modell gebaut (**Baseline**), damit wir später messen können,
  ob unsere Verbesserungen etwas bringen.

**Ergebnis in einem Satz:** Unser einfaches Startmodell erkennt die Pflanze und das
Stadium jeweils zu rund **83 %** richtig (gemessen als *Balanced Accuracy*), beide
zusammen zu **69 %** – und wir wissen jetzt genau, wo es noch hakt.

---

## 2. Grundbegriffe – ganz einfach erklärt

### Rund ums Licht und die Pflanzen

| Begriff | Einfach erklärt |
|---|---|
| **Wellenlänge (nm)** | „Farbe“ des Lichts, gemessen in Nanometern. 400–700 nm sieht das Auge (blau → rot), darüber ist Infrarot. |
| **Reflexion (%)** | Wie viel Prozent des Sonnenlichts bei einer Wellenlänge zurückgeworfen wird. 10 % = dunkel, 60 % = hell. |
| **Spektrum** | Die Kurve „Reflexion über Wellenlänge“ für einen Bildpunkt. Unsere eigentlichen Messdaten. |
| **Band** | Ein einzelner Messkanal des Sensors, z. B. „X671“ = Reflexion bei 671 nm. Jede Spalte `X…` in den Daten ist ein Band. |
| **Hyperspektral** | Sehr viele, schmale Bänder (hier ~10 nm breit). Gegenteil: **multispektral** = wenige breite Bänder (z. B. Sentinel-2 mit 13). |
| **VIS** | Sichtbares Licht (400–700 nm). Gesunde Pflanzen schlucken Blau und vor allem Rot (für die Fotosynthese), Grün wird etwas mehr reflektiert → Pflanzen sehen grün aus. |
| **Chlorophyll-Mulde (~670 nm)** | Tiefe Stelle im Rot: Blattgrün schluckt das Rotlicht. Je tiefer, desto mehr gesundes Grün. |
| **Rote Kante (Red Edge, 700–760 nm)** | Der steile Anstieg der Kurve vom Rot ins Infrarot. Typisches „Fingerabdruck-Merkmal“ von Vegetation. Steil und weit rechts = viel gesunde Blattmasse. |
| **NIR (Nahinfrarot, 760–1300 nm)** | Hier reflektieren Blätter sehr stark (Zellstruktur). Viel Blattmasse → hohes NIR-Plateau. |
| **SWIR (kurzwelliges Infrarot, 1500–2400 nm)** | Hier schluckt **Wasser** im Blatt Licht. Saftige Pflanzen = niedriges SWIR, trockene Pflanzen / Boden / Stroh = hohes SWIR. |
| **Wasserdampfbanden** | Bereiche (~1130, ~1400, ~1900 nm), in denen die **Luft** fast alles Licht schluckt. Dort kommt am Satelliten kein brauchbares Signal an → diese Bänder sind in den Daten leer. |
| **NDVI** | Der bekannteste Vegetationsindex: (NIR − Rot) / (NIR + Rot). Werte nahe 0 = Boden, ~0,3 = wenig Pflanze, 0,7–0,8 = dichter, grüner Bestand. |
| **Vegetationsindex** | Eine Formel aus wenigen Bändern, die eine Pflanzeneigenschaft beschreibt (Grünheit, Wasser, Seneszenz …). Wir haben 31 davon berechnet. |
| **Phänologie** | Der jahreszeitliche Ablauf des Pflanzenwachstums (Keimen → Wachsen → Blühen → Reifen → Ernte). |
| **AEZ** | *Agroökologische Zone*: eine Region mit ähnlichem Klima und Boden, als Nummer (2, 5, 6, 7, 8, 9, 10). |
| **Hyperion / EO-1** | NASA-Testsatellit (2000–2017), einer der ersten Hyperspektral-Sensoren im All. 220 Bänder, 400–2500 nm, 30-m-Pixel. |

### Die 6 Wachstumsstadien (Stages)

| Name in den Daten | Deutsch | Wie sieht das Feld aus? |
|---|---|---|
| `Emerge_VEarly` | Auflaufen / sehr früh | Winzige Pflänzchen, man sieht vor allem **Boden** |
| `Early_Mid` | früh bis mittel vegetativ | Pflanzen wachsen, Boden wird weniger sichtbar |
| `Late` | spät vegetativ | Feld fast komplett **grün bedeckt** |
| `Critical` | kritisch (Blüte/Fruchtbildung) | Voll entwickelt, wichtigste Phase für den Ertrag |
| `Mature_Senesc` | Reife / Seneszenz | Pflanzen werden **gelb/braun**, trocknen ab |
| `Harvest` | Ernte | Abgeerntet oder kurz davor – wieder viel **Boden/Stroh** |

### Rund ums maschinelle Lernen

| Begriff | Einfach erklärt |
|---|---|
| **Klassifikation** | Das Modell ordnet jede Probe einer Kategorie (Klasse) zu, z. B. „Mais“. |
| **Klasse** | Eine mögliche Antwort. Crop hat 5, Stage 6, die Kombination Crop×Stage hat **23** (nicht 30, weil manche Kombinationen nicht vorkommen). |
| **Merkmal / Feature** | Eine Eingabegröße für das Modell. Bei uns: 131 Bänder + AEZ + Monat = 133 Merkmale. |
| **Training / Test** | Mit den Trainingsdaten lernt das Modell; mit den Testdaten (die es nie gesehen hat) prüfen wir, wie gut es ist. Wie Üben mit Übungsaufgaben und Prüfen mit einer neuen Klausur. |
| **70/30-Split** | 70 % der gelabelten Daten zum Lernen, 30 % zum Prüfen. |
| **stratifiziert** | Beim Aufteilen wird darauf geachtet, dass jede Klasse in beiden Teilen im gleichen Verhältnis vorkommt. Sonst landen die 11 seltenen Proben evtl. alle auf einer Seite. |
| **Baseline** | Ein bewusst einfaches erstes Modell. Der **Referenzpunkt**: Alles, was wir später bauen, muss besser sein als die Baseline. |
| **Random Forest** | Viele (bei uns 500) Entscheidungsbäume, die jeweils auf zufälligen Teilen der Daten lernen und dann **abstimmen**. Robust, braucht kaum Einstellungen – der Klassiker für eine Baseline. |
| **Entscheidungsbaum** | Ein Ablauf aus Ja/Nein-Fragen, z. B. „Reflexion bei 800 nm > 40 %? → ja → AEZ = 7? → …“. |
| **Klassengewichte** | Seltene Klassen zählen beim Lernen stärker, damit das Modell sie nicht einfach ignoriert. |
| **Klassenungleichgewicht** | Manche Klassen sind viel häufiger als andere (Mais 2.097 Proben, Reis 93). |
| **Accuracy (Genauigkeit)** | Anteil richtiger Vorhersagen. **Problem:** Bei Ungleichgewicht trügerisch – wer immer „Mais“ sagt, hat schon 37,5 % richtig, ohne etwas zu können. |
| **Recall (Trefferquote) je Klasse** | Von allen echten Reis-Proben: wie viele hat das Modell als Reis erkannt? |
| **Precision (Präzision)** | Von allem, was das Modell „Reis“ nennt: wie viel ist wirklich Reis? |
| **Balanced Accuracy (BAcc)** | **Durchschnitt der Trefferquoten aller Klassen.** Jede Klasse zählt gleich, egal wie groß. Der „immer Mais“-Rater hätte nur 1/5 = **20 %**. **Das ist die Hauptmetrik der Bewertung.** |
| **F1** | Kombination aus Precision und Recall (harmonisches Mittel). |
| **Macro-F1** | F1 je Klasse ausrechnen, dann Durchschnitt – jede Klasse zählt gleich. |
| **Samples-F1** | Pro Probe: Pflanze **und** Stadium richtig = 1, nur eins richtig = 0,5, nichts richtig = 0. Dann Durchschnitt über alle Proben. |
| **Konfusionsmatrix** | Tabelle „wahr (Zeile) gegen vorhergesagt (Spalte)“. Auf der Diagonalen stehen die Treffer, daneben die Verwechslungen. |
| **Leakage (Datenleck)** | Wenn beim Lernen versehentlich Information aus den Testdaten benutzt wird. Dann sieht das Ergebnis besser aus, als es ist – wie wenn man die Klausur vorher kennt. |
| **Overfitting** | Das Modell lernt die Trainingsdaten auswendig statt allgemeiner Regeln. |
| **Cluster** | Eine Gruppe von sehr ähnlichen Proben. **KMeans** ist ein Verfahren, das Daten automatisch in solche Gruppen einteilt. |
| **PCA (Hauptkomponentenanalyse)** | Fasst viele zusammenhängende Spalten zu wenigen „Hauptrichtungen“ zusammen. Zeigt, wie viel echte, unterschiedliche Information in den Daten steckt. |
| **Korrelation (r)** | Wie stark zwei Größen zusammenhängen (1 = gehen völlig gleich, 0 = kein Zusammenhang). |
| **kNN (k-nächste Nachbarn)** | Einfaches Modell: schaut, welche Klasse die k ähnlichsten Trainingsproben haben. Wir nutzen es in der EDA als „Messgerät“ für die Trennbarkeit. |
| **Ausreißer** | Proben, die sehr anders aussehen als der Rest ihrer Klasse. |
| **LOF (Local Outlier Factor)** | Ausreißer-Verfahren: Liegt ein Punkt in einer viel dünner besiedelten Gegend als seine Nachbarn? LOF > 2 = mehr als doppelt so einsam → verdächtig. |
| **Adversarielle Validierung** | Trick: Man trainiert ein Modell darauf, Trainings- von Testdaten zu unterscheiden. Schafft es das nicht (AUC ≈ 0,5 = Münzwurf), stammen beide aus demselben „Topf“. |
| **AUC** | Maß von 0,5 (Raten) bis 1,0 (perfekt), wie gut ein Modell zwei Gruppen unterscheidet. |
| **Interpolation** | Eine Lücke aus den Nachbarwerten auffüllen (bei uns: gerade Linie zwischen den Nachbarbändern). |

---

## 3. Die Daten: Was steht in den Dateien?

Beide Dateien liegen in `data/raw/` und werden **nie verändert** (Bereinigung passiert
nur im Programm).

**`train.csv` – 5.591 Zeilen, mit Lösungen (gelabelt)**

| Spalte | Bedeutung |
|---|---|
| (erste, ohne Namen) | laufende Nummer, wird ignoriert |
| `AEZ` | agroökologische Zone (Zahl) |
| `Month` | Aufnahmemonat (5 = Mai … 10 = Oktober) |
| `Crop` | **Lösung 1**: Pflanze (`corn`, `cotton`, `rice`, `soybean`, `winter_wheat`) |
| `Stage` | **Lösung 2**: Stadium (siehe Tabelle oben) |
| `X427` … `X2395` | 198 Bänder: Reflexion in % bei 427 nm … 2395 nm |

**`test.csv` – 1.397 Zeilen, ohne Lösungen.** Gleiche Spalten, nur ohne `Crop` und
`Stage`. Für diese Zeilen sollen wir am Ende Vorhersagen abgeben. Laut
Aufgabenstellung kommt gegen Projektende noch ein weiterer Datensatz ohne Labels zur
Bewertung.

**Eine Zeile = ein Bildpunkt (30 × 30 m) auf einem Feld zu einem Zeitpunkt.** Es gibt
**keine** Koordinaten, Feld-Nummern oder Aufnahmedaten – das wird später wichtig
(Cluster-Split, Abschnitt 9).

Die Daten stammen vermutlich aus der GHISA-Spektralbibliothek (USGS, „Global
Hyperspectral Imaging Spectral-library of Agricultural crops“) – daher auch die
Benennung der Stadien.

---

## 4. Rundgang durch den Ordner

```
Erster_Meilenstein_Fortschritt/
├── ANLEITUNG.md          ← diese Datei
├── README.md             ← Kurzüberblick (für Prüfer, Git)
├── requirements.txt      ← Liste der Python-Pakete mit Versionen
├── data/raw/             ← Rohdaten train.csv, test.csv (nicht anfassen)
├── src/dp2/              ← unser Python-Paket: die eigentliche Logik
├── scripts/              ← die Programme, die man startet
├── notebooks/            ← Jupyter-Notebooks zum Anschauen und Vorführen
├── results/figures/      ← alle erzeugten Abbildungen (PNG)
├── results/tables/       ← alle erzeugten Tabellen und Kennzahlen
└── reports/              ← Kurzreport Meilenstein 1, offene Fragen
```

### `src/dp2/` – das Paket (hier steckt das Wissen)

| Datei | Was sie macht |
|---|---|
| `config.py` | Zentrale Einstellungen: Dateipfade, Zufallszahl `SEED = 42`, Reihenfolge und deutsche Namen der Klassen, Farben für die Abbildungen. |
| `data.py` | **Das Pre-Processing.** Lädt die CSVs, wirft leere Bänder raus, füllt einzelne Lücken, entfernt Duplikate, baut die kombinierte Klasse (z. B. `corn__Critical`). |
| `features.py` | Baut aus einer Tabelle die Zahlenmatrix fürs Modell (Bänder + AEZ + Monat). Enthält außerdem die 31 Vegetationsindizes (NDVI usw.), die wir in der EDA benutzen. |
| `models.py` | „Modellfabrik“: liefert auf Zuruf ein Modell (`rf` = Random Forest, `dummy` = Zufallsrater, `logreg`, `knn`). |
| `strategies.py` | Wie Pflanze und Stadium zusammen vorhergesagt werden: **Flat** (eine kombinierte Klasse) oder **Separate** (zwei getrennte Modelle). |
| `evaluation.py` | Die beiden 70/30-Aufteilungen (stratifiziert und Cluster-Split) und das Auswerten eines Modells. |
| `metrics.py` | Berechnet Balanced Accuracy, Macro-F1, Samples-F1 auf allen drei Ebenen. |
| `viz.py` | Helfer für Abbildungen (Konfusionsmatrix zeichnen, speichern). |

### `scripts/` – was man startet

| Datei | Was passiert | Dauer |
|---|---|---|
| `01_eda.py` | Datenanalyse: erzeugt 12 Abbildungen `eda_*.png` und die Kennzahlen `eda_facts.json`, `outlier_flags.csv`, `class_counts_crop_stage.csv` | ~20 s |
| `02_baseline.py` | Trainiert und bewertet die Baseline (4 Varianten × 2 Splits), erzeugt `m1_baseline_*` | ~10 s |
| `make_notebooks.py` | Baut die beiden Notebooks neu und führt sie aus | ~10 s |
| `run_all.sh` | Startet alle drei nacheinander | < 1 min |

### `notebooks/`

* `01_EDA.ipynb` – die Datenanalyse zum Durchblättern, mit Erklärtexten und Bildern.
* `02_Baseline_Demo.ipynb` – **der „Demo-Run“ für den Meilenstein**: lädt die Daten,
  trainiert die Baseline live und zeigt die Zahlen. Gut zum Vorführen.

### `reports/`

* `Meilenstein1_Kurzreport.md` – **das offizielle Abgabe-Dokument** für Meilenstein 1.
* `Fragen_fuer_Kickoff.md` – Unklarheiten in der Aufgabenstellung, die wir notiert haben.

---

## 5. Bedienung Schritt für Schritt

Alle Befehle im **Terminal** (Mac: Programm „Terminal“), jeweils eine Zeile eingeben und
Enter drücken.

**Schritt 1 – in den Ordner wechseln**

```bash
cd ~/Downloads/DP2_Hyperspektral/Erster_Meilenstein_Fortschritt
```

**Schritt 2 – Python-Umgebung einrichten (nur beim ersten Mal)**

Eine „virtuelle Umgebung“ (`.venv`) ist ein eigener kleiner Python-Ordner nur für dieses
Projekt, damit die Paketversionen genau stimmen.

```bash
python3 -m venv .venv
```

```bash
.venv/bin/pip install -r requirements.txt
```

> Getestet mit Python 3.14. Wenn `pip` bei einer Version meckert, liegt das meist an
> einer älteren Python-Version – dann `python3 --version` prüfen.

**Schritt 3 – alles laufen lassen**

```bash
bash scripts/run_all.sh
```

Im Terminal laufen dann Kennzahlen und die Baseline-Ergebnisse durch. Danach sind
`results/figures/`, `results/tables/` und `notebooks/` frisch erzeugt.

**Einzelne Teile starten:**

```bash
.venv/bin/python scripts/01_eda.py
```

```bash
.venv/bin/python scripts/02_baseline.py
```

**Schritt 4 – Notebooks anschauen**

```bash
.venv/bin/jupyter notebook notebooks/
```

Es öffnet sich der Browser. `02_Baseline_Demo.ipynb` anklicken, oben
„Run → Run All Cells“. Alternativ die `.ipynb`-Dateien in VS Code öffnen.

**Schritt 5 – Ergebnisse anschauen.** Die Bilder in `results/figures/` einfach per
Doppelklick öffnen. Die Tabellen (`.csv`) lassen sich mit Excel/Numbers öffnen.

**Gut zu wissen**

* Die Ergebnisse sind **reproduzierbar**: Wer die Skripte startet, bekommt exakt
  dieselben Zahlen, weil der Zufall mit `SEED = 42` festgelegt ist.
* Kaputt machen kann man nichts: Die Rohdaten werden nie überschrieben, alle
  Ergebnisse werden einfach neu erzeugt.

---

## 6. Was wir gemacht haben – der rote Faden

Die Aufgabenstellung verlangt für Meilenstein 1 (08.10.):

1. Kurzreport zu **Problemverständnis** (Domäne & Business-Ziel) und **Data Understanding**,
2. eine **erste Pre-Processing-Pipeline**,
3. einen **ersten Baseline-Klassifikator mit 70/30-Split**, Code + kurzer Demo-Run.

So sind wir vorgegangen:

```
Aufgabe verstehen  →  Daten anschauen (EDA)  →  Daten bereinigen  →  Baseline bauen  →  auswerten
   (Abschnitt 1)        (01_eda.py)              (data.py)            (02_baseline.py)   (Konfusionsmatrix,
                                                                                          Cluster-Split)
```

**Die EDA hat 10 Fragen beantwortet:**

1. Wie sind die Klassen verteilt?
2. Was verraten Region (AEZ) und Monat?
3. Wie sehen die Spektren der Pflanzen aus?
4. Wie verändert sich das Spektrum über die Stadien?
5. Was zeigen Vegetationsindizes?
6. Wie viel echte Information steckt in den 131 Bändern (Korrelation, PCA)?
7. Wie gut lassen sich die Pflanzen allein am Spektrum trennen?
8. Gibt es Ausreißer oder fehlerhafte Messungen?
9. Sind Trainings- und Testdaten vergleichbar?
10. Wann im Jahr kommt welches Stadium vor?

**Das Pre-Processing (Version 1)** in `src/dp2/data.py`:

1. Die namenlose Nummern-Spalte entfernen.
2. **67 komplett leere Bänder entfernen** → 198 − 67 = **131 nutzbare Bänder**.
3. **48 einzelne fehlende Werte** (in 44 Zeilen, 6 Bändern) je Spektrum mit einer
   geraden Linie zwischen den Nachbarbändern auffüllen.
4. **2 doppelte Zeilen entfernen** → 5.589 Trainingsproben.
5. Merkmale fürs Modell: 131 Reflexionswerte + AEZ + Monat.

**Die Baseline** in `scripts/02_baseline.py`: Random Forest, zwei Aufteilungsarten,
vier Vergleichsvarianten (Abschnitt 8).

---

## 7. Die Erkenntnisse – Bild für Bild

Zu jeder Abbildung in `results/figures/`: **Was sieht man?** und **Was sagt man dazu?**

### 7.1 Klassenverteilung – `eda_class_distribution.png`

**Was man sieht:** Balken mit der Anzahl Proben je Pflanze, je Stadium und je
Kombination.

| Pflanze | Proben |
|---|---|
| Mais | 2.097 |
| Sojabohne | 1.669 |
| Winterweizen | 1.072 |
| Baumwolle | 658 |
| Reis | **93** |

* Mais : Reis = **22 : 1**. Größte zu kleinster Kombination = **61 : 1**.
* Nur **23 von 30** denkbaren Kombinationen kommen vor (z. B. Reis nur in *Early_Mid*
  und *Late*, Winterweizen nie in *Early_Mid* oder *Harvest*).
* Kleinste Kombinationen: Baumwolle/Ernte (**11**), Winterweizen/Late (30), Reis/Late (41).

**Was man sagt:** „Die Daten sind stark unausgeglichen. Deshalb benutzen wir
Klassengewichte, stratifizierte Splits und als Hauptmaß die Balanced Accuracy, bei der
seltene Klassen genauso zählen wie häufige.“

### 7.2 Metadaten – `eda_metadata.png`

**Was man sieht:** Welche Pflanze kommt in welcher Zone (AEZ) und in welchem Monat vor.

* **Reis** nur in AEZ 7 und nur im August.
* **Baumwolle** nur in AEZ 2, 5, 9.
* **Winterweizen** nur in AEZ 5 und 9.

**Wichtigstes Zahlenexperiment:** Wenn man **nur** in einer Tabelle nachschlägt
„welche Pflanze ist in dieser Zone in diesem Monat am häufigsten?“ – ganz ohne
Spektrum –, erreicht man schon eine Balanced Accuracy von **0,72 (Pflanze)** und
**0,65 (Stadium)**.

**Was man sagt:** „AEZ und Monat tragen sehr viel Information. Die Aufgabenstellung
erlaubt sie ausdrücklich, also nutzen wir sie. Die eigentliche Aufgabe des Spektrums
ist, die Fälle zu trennen, die in derselben Zone im selben Monat vorkommen.“

### 7.3 Spektren je Pflanze – `eda_spectra_crop.png`

**Was man sieht:** Eine Kurve je Pflanze (Median, also der „typische“ Verlauf), der
blasse Bereich zeigt die Streuung (mittlere 50 %). Graue Streifen = entfernte Bänder.

* Alle haben die typische Pflanzenform: niedrig im Sichtbaren, Mulde bei ~670 nm,
  steiler Anstieg (rote Kante), hohes Plateau im NIR.
* **Reis** hat das höchste NIR (~60 %) und das niedrigste SWIR → sehr dichter,
  wasserreicher Bestand (Reis steht im Wasser).
* **Baumwolle und Winterweizen** haben niedriges NIR, aber **hohes SWIR** → viel
  sichtbarer Boden bzw. trockeneres Material.
* Mais und Soja liegen dazwischen und ähneln sich stark.
* Die Streuung (blasse Bänder) ist groß und überlappt → **eine Pflanze hat nicht
  „das eine“ Spektrum**, weil es stark vom Stadium abhängt.

**Was man sagt:** „Die Unterschiede liegen vor allem im NIR und im SWIR, also in
Bereichen, die das Auge nicht sieht. Genau dafür ist ein Hyperspektralsensor da.“

**Die grauen Streifen erklären können:** Dort liegen die **Wasserdampfbanden der
Atmosphäre** (~1130, ~1400, ~1900 nm), der Übergang zwischen den beiden
Hyperion-Detektoren (925–973 nm) und die verrauschten Ränder. Dort kommt kein
brauchbares Licht an – diese Bänder sind deshalb in **Training und Test komplett leer**.
Das ist kein Datenfehler, sondern Physik.

### 7.4 Spektren je Stadium – `eda_spectra_stage_per_crop.png`

**Das wichtigste Bild für das Verständnis.** Für jede Pflanze eine Kurve je Stadium.

* **Auflaufen und Ernte:** fast flache Kurve, kaum rote Kante, hohes SWIR → der
  Satellit sieht hauptsächlich **Boden**. NDVI nur 0,07–0,15.
* **Late und Critical:** tiefe Chlorophyll-Mulde, steile rote Kante, NIR 50–65 %,
  niedriges SWIR (Blattwasser) → **volle grüne Bedeckung**. NDVI 0,65–0,80.
* **Reife/Seneszenz:** Rot steigt wieder (Chlorophyll wird abgebaut), SWIR steigt
  (Pflanze trocknet).
* **Ausnahme Baumwolle:** selbst in *Critical* nur NDVI ≈ 0,37 – Baumwolle steht
  lückig auf hellen, trockenen Böden.

**Was man sagt:** „Das Spektrum erzählt den Lebenslauf der Pflanze: erst Boden, dann
immer grüner, dann gelb und trocken, dann wieder Boden. Das Stadium verändert das
Spektrum oft stärker als die Pflanzenart.“

### 7.5 Vegetationsindizes – `eda_indices.png`

**Was man sieht:** Drei Boxplot-Diagramme – **NDVI** (Grünheit), **NDMI** (Blattwasser,
860/1650 nm) und **PSRI** (Seneszenz/Vergilbung) –, je Stadium und darin je Pflanze
eine farbige Box (die Box zeigt, wo die mittleren 50 % der Werte liegen).

* NDVI steigt vom Auflaufen bis *Late/Critical* stark an und fällt zur Reife und Ernte wieder ab.
* NDMI verläuft ähnlich (grüne Pflanzen sind wasserreich).
* PSRI steigt erst bei Reife/Seneszenz an – er zeigt das Vergilben.

**Was man sagt:** „Die Indizes bestätigen den Verlauf aus 7.4 mit einer einzigen Zahl.
Ob sie dem Modell zusätzlich helfen, prüfen wir in Meilenstein 2 – die Baseline nutzt
sie bewusst noch nicht.“

### 7.6 Korrelation und PCA – `eda_correlation_pca.png`, `eda_pca_scatter.png`

**Was man sieht:** Links eine Matrix, wie stark die Bänder untereinander
zusammenhängen (fast alles dunkel = stark). Rechts: wie viel Information die ersten
Hauptkomponenten zusammenfassen.

* Benachbarte Bänder korrelieren im Median mit **r = 0,999** – fast identisch.
* **3 Hauptkomponenten** erklären schon **96 %**, **10 erklären 99,7 %** der Unterschiede.
* Im PCA-Streubild (`eda_pca_scatter.png`) sieht man jede Probe als Punkt auf den
  ersten beiden Hauptkomponenten (zusammen 92 %), links nach Pflanze, rechts nach
  Stadium eingefärbt. **Rechts ordnen sich die Stadien deutlich von links nach rechts**:
  grüne Bestände (*Late*, *Critical*) links, Reife und Ernte/Auflaufen (Boden) rechts.
  PC1 ist also im Grunde eine „Wie viel grüne Pflanze vs. Boden“-Achse. **Links sind
  die Pflanzen stark vermischt** – nur Soja und Mais bilden erkennbare Häufungen.

**Was man sagt:** „In den 131 Bändern steckt viel Doppelung. Das ist eine gute
Nachricht für Meilenstein 3 (Datenreduktion): Man kommt vermutlich mit viel weniger
Bändern aus.“ – **Vorsicht:** 96 % der *Varianz* heißt nicht 96 % der *Information
zur Unterscheidung*. Feine Unterschiede können gerade in den kleinen Komponenten stecken.

### 7.7 Trennbarkeit der Pflanzen – `eda_crop_separability_by_stage.png`, `eda_knn_crop_confusion.png`

**Was man sieht:** Wir haben ein ganz einfaches Modell (5-nächste-Nachbarn, **nur**
Spektrum, ohne AEZ/Monat) die Pflanze bestimmen lassen – getrennt nach Stadium.

| Stadium | Pflanze richtig erkannt |
|---|---|
| Late (voll grün) | **90 %** |
| Critical | 87 % |
| Reife | 79 % |
| Early_Mid | 79 % |
| Auflaufen | **71 %** |
| Ernte | **63 %** |

**Was man sagt (zentrale Erkenntnis!):** „**Wo der Satellit Boden sieht, kann man die
Pflanze kaum erkennen.** Ein frisch gesätes Maisfeld und ein frisch gesätes Sojafeld
sehen von oben gleich aus – nämlich wie Erde. Deshalb muss man das Stadium
mitdenken: Ein Modell, das Pflanze und Stadium gemeinsam betrachtet, ist im Vorteil.
Das ist auch die Begründung für den hierarchischen bzw. gemeinsamen Ansatz.“

### 7.8 Ausreißer – `eda_outliers.png`, Tabelle `outlier_flags.csv`

Drei Verfahren ausprobiert:

1. **Robuste Mahalanobis-Distanz** (klassisches Verfahren): markiert **2.013** Proben,
   also über ein Drittel! → Das Verfahren **passt nicht**, weil jede Klasse aus mehreren
   „Wolken“ besteht (verschiedene Felder, Regionen, Szenen) – die Klassen sind
   *multimodal*. Das Verfahren nimmt aber nur *eine* Wolke an.
2. **Local Outlier Factor** (dichtebasiert, verträgt mehrere Wolken): **39** Proben.
3. **Plausibilitätsregel:** „volle Bedeckung (*Late/Critical*), aber NDVI < 0,2“ – also
   ein Bodenspektrum, obwohl das Feld grün sein müsste: **33** Proben, davon 27
   Baumwolle/Critical.

Zusammen **72** verdächtige Proben (1,3 %).

**Was man sagt:** „Wir haben uns die verdächtigen Spektren angeschaut: Sie sind
physikalisch plausibel – hellere Bestände, Mischpixel am Feldrand, lückige Baumwolle.
Deshalb löschen wir sie **nicht blind**, sondern prüfen in Meilenstein 2 per
Kreuzvalidierung, ob das Entfernen überhaupt etwas bringt.“

### 7.9 Training vs. Test – `eda_train_vs_test.png`

* **Adversarielle Validierung:** Ein Modell sollte erkennen, ob eine Zeile aus
  `train.csv` oder `test.csv` stammt. Ergebnis: **AUC = 0,50** – reines Raten.
* Der Abstand jeder Probe zur ähnlichsten Trainingsprobe ist für Test- und
  Trainingsdaten praktisch gleich (Median 1,28 vs. 1,27).
* Die Anteile von Monaten und Zonen sind in beiden gleich verteilt.

**Was man sagt:** „Der Testdatensatz ist ein zufälliger Ausschnitt aus demselben Topf
wie das Training. Deshalb ist ein stratifizierter Zufallssplit eine realistische
Schätzung für die Testnote.“

### 7.10 Phänologie – `eda_phenology.png`

**Was man sieht:** Welches Stadium in welchem Monat vorkommt, je Pflanze.

* Mais/Soja: Frühjahr Auflaufen → Sommer Blüte → Herbst Reife/Ernte – wie erwartet.
* **Winterweizen** läuft im **Herbst** (September/Oktober) auf, überwintert, und ist im
  Frühsommer reif. Deshalb gibt es „Auflaufen“ bei Winterweizen im Oktober.

**Was man sagt:** „Der Monat allein verrät schon viel über das Stadium – aber nur
zusammen mit der Pflanze, weil Winterweizen genau gegenläufig wächst.“

---

## 8. Die Baseline – Ergebnisse verstehen

### Was genau ist die Baseline?

* **Modell:** Random Forest mit 500 Bäumen und Klassengewichten.
* **Eingabe:** 131 Bänder + AEZ + Monat (keine weiteren Tricks, kein Tuning).
* **Ziel:** die **kombinierte Klasse** Crop×Stage (23 Klassen), z. B. `corn__Critical`.
  Aus der Vorhersage lesen wir dann Pflanze und Stadium ab.
* **Aufteilung:** 70 % lernen, 30 % prüfen.

### Die beiden 70/30-Aufteilungen

1. **Stratifiziert zufällig** (3.912 Lernen / 1.677 Prüfen): Jede Zeile kommt zufällig
   auf eine Seite, jede Klasse im richtigen Verhältnis. Entspricht dem Testdatensatz
   (siehe 7.9).
2. **Cluster-Split** (3.714 / 1.875): Die Aufgabenstellung verlangt einen
   „Clusterplot-Split“. Idee: Nachbarpixel desselben Feldes sind fast identisch. Liegt
   eines im Training und sein Zwilling im Test, „erkennt“ das Modell ihn nur wieder.
   Weil die Daten **keine Feld-Nummern** haben, bilden wir Ersatz-Felder:
   * Proben werden nach (AEZ, Monat, Pflanze, Stadium) gruppiert,
   * innerhalb jeder Gruppe fasst KMeans spektral ähnliche Proben zu Clustern
     (~20 Proben) zusammen,
   * **ganze Cluster** wandern in den Test, bis ~30 % jeder Klasse erreicht sind.

   So muss das Modell auf „neue Felder“ verallgemeinern. Das ist die **strengere**
   Prüfung.

### Die Ergebnisse (Datei `results/tables/m1_baseline_results.csv`)

**Stratifizierter Split:**

| Variante | BAcc Pflanze | BAcc Stadium | BAcc Kombi | Samples-F1 |
|---|---|---|---|---|
| Zufallsrater (Untergrenze) | 0,197 | 0,152 | 0,040 | 0,232 |
| RF nur Spektrum | 0,782 | 0,765 | 0,601 | 0,808 |
| **RF Spektrum + AEZ + Monat = Baseline** | **0,827** | **0,829** | **0,692** | **0,858** |
| RF zwei getrennte Modelle | 0,823 | 0,786 | 0,623 | 0,841 |

**Cluster-Split:**

| Variante | BAcc Pflanze | BAcc Stadium | BAcc Kombi | Samples-F1 |
|---|---|---|---|---|
| Zufallsrater | 0,192 | 0,164 | 0,046 | 0,232 |
| RF nur Spektrum | 0,532 | 0,524 | 0,295 | 0,628 |
| **Baseline** | **0,652** | **0,598** | **0,390** | **0,699** |
| RF zwei getrennte Modelle | 0,561 | 0,586 | 0,328 | 0,685 |

### Wie liest man das?

1. **Die Baseline ist weit besser als Raten** (0,69 statt 0,04 auf der Kombi-Ebene) –
   das Spektrum enthält also klar die gesuchte Information.
2. **Metadaten helfen:** Mit AEZ + Monat steigt die Kombi-BAcc von 0,60 auf 0,69
   (+0,09).
3. **Gemeinsam ist besser als getrennt:** Zwei unabhängige Modelle (eins für Pflanze,
   eins für Stadium) kommen nur auf 0,62. Grund: Das Stadium sieht je Pflanze anders
   aus (Baumwolle in Blüte ≠ Mais in Blüte); wer beides unabhängig rät, verschenkt das.
   Außerdem können getrennte Modelle **unmögliche Kombinationen** ausgeben (z. B.
   „Reis/Ernte“) – die kombinierte Klasse kann das nicht.
4. **Der Cluster-Split kostet 0,30 Punkte** (0,69 → 0,39). Ein großer Teil der Leistung
   beim Zufallssplit kommt also vom „Wiedererkennen“ fast gleicher Nachbarpixel. Für
   die **Projektbewertung** (Test = Zufallsausschnitt) ist der stratifizierte Split die
   richtige Schätzung; für eine **echte Anwendung auf neuen Feldern** müsste man mit
   deutlich weniger rechnen. Wir berichten deshalb immer beide Zahlen.

### Konfusionsmatrix lesen – `m1_baseline_confusion.png`

Zeile = was es wirklich ist, Spalte = was das Modell gesagt hat, Zahlen = Anteil der
Zeile (also Trefferquote auf der Diagonalen).

**Pflanze (links):**
* Mais 90 %, Winterweizen 87 %, Baumwolle 83 %, Soja 83 %, **Reis nur 70 %**.
* **Reis wird zu 22 % als Mais erkannt** – Reis hat nur 93 Proben und kommt in
  derselben Zone (AEZ 7) wie Mais vor.
* **Soja wird zu 13 % als Mais erkannt** – die beiden Spektren ähneln sich (7.3).

**Stadium (rechts):**
* Late und Critical je 92 % (voll grün = gut erkennbar).
* **Ernte nur 70 %** – wird mit Reife (17 %) und Auflaufen (13 %) verwechselt: alles
  „Boden mit wenig Pflanze“.
* Verwechslungen fast nur zwischen **benachbarten** Stadien – fachlich sinnvoll, die
  Übergänge sind fließend.

**Kombi-Ebene** (`m1_baseline_confusion_combo.png`, Tabelle `m1_baseline_per_class.csv`),
die schwächsten Klassen:

| Klasse | Trefferquote | Warum vermutlich |
|---|---|---|
| Baumwolle / Ernte | 0,33 | nur 11 Proben insgesamt, 3 im Test |
| Soja / Auflaufen | 0,34 | Boden sieht überall gleich aus |
| Baumwolle / Reife | 0,37 | wenige Proben, lückige Bestände |
| Soja / Ernte | 0,45 | Boden/Stroh |

**Muster:** Es scheitert genau da, wo die EDA es vorhergesagt hat – bei **seltenen
Klassen** und bei **bodendominierten Stadien**.

---

## 9. Warum haben wir das so gemacht? (Entscheidungen)

**Warum die 67 Bänder löschen?** Sie sind in Training **und** Test komplett leer
(physikalisch kein Signal, siehe 7.3). Ein Band ohne Werte kann nichts beitragen.

**Warum Lücken interpolieren statt z. B. mit dem Mittelwert füllen?** Ein Spektrum ist
eine glatte Kurve – der Nachbarwert ist die beste Schätzung. Außerdem braucht das keine
Information aus anderen Zeilen, also **kein Datenleck** zwischen Training und Test. Es
betrifft nur 48 Einzelwerte.

**Warum Duplikate entfernen?** Eine doppelte Zeile könnte einmal im Training und einmal
im Test landen – das Modell hätte die Lösung schon gesehen.

**Warum Random Forest als Baseline?** Robust, braucht keine Skalierung, kommt mit vielen
stark korrelierten Merkmalen klar, kann Klassengewichte, funktioniert ohne Tuning. Der
Standard-Startpunkt in der Literatur zur Pflanzenklassifikation. Ein zu gutes Startmodell
wäre als Baseline sogar ungünstig – es soll ein ehrlicher Referenzpunkt sein.

**Warum keine Skalierung/Normalisierung?** Entscheidungsbäume sind davon unabhängig –
sie vergleichen nur „größer/kleiner als“. Für andere Modelle (SVM, neuronale Netze) kommt
das in Meilenstein 2.

**Warum die kombinierte Klasse (flach) statt hierarchisch?** Für die Baseline ist sie die
einfachste Variante, die trotzdem keine unmöglichen Paare erzeugen kann, und sie war im
Vergleich besser als getrennte Modelle. Echte hierarchische Varianten (erst Pflanze,
dann Stadium je Pflanze) vergleichen wir in Meilenstein 2.

**Warum Balanced Accuracy auf drei Ebenen?** Die Aufgabenstellung sagt nicht, ob Pflanze,
Stadium oder die Kombination bewertet wird. Wir berichten alle drei und haben die Frage
für den Kickoff notiert.

**Warum Klassengewichte?** Ohne sie lernt das Modell vor allem Mais und Soja und
ignoriert Reis – das bestraft die Balanced Accuracy hart.

**Warum Seed 42?** Damit jeder dieselben Zahlen bekommt (Reproduzierbarkeit). Die Zahl
selbst ist egal.

---

## 10. Grenzen und offene Punkte

* **Keine Feld-IDs:** Der Cluster-Split ist nur ein Ersatz für einen echten Feld-Split.
* **Seltene Klassen:** Bei 11 Proben (Baumwolle/Ernte) schwanken die Ergebnisse stark;
  3 Testproben sind keine verlässliche Aussage.
* **Ein einzelner 70/30-Split** ist etwas zufallsabhängig. Für Meilenstein 2 stellen wir
  auf eine 5-fache Kreuzvalidierung um (fünfmal anders aufteilen, Mittelwert bilden).
* **Offene Fragen zur Aufgabenstellung** (`reports/Fragen_fuer_Kickoff.md`), z. B. auf
  welcher Ebene die Balanced Accuracy gewertet wird und was genau mit „Clusterplot-Split“
  gemeint ist.
* **Ausreißer** sind markiert, aber noch nicht entschieden.

---

## 11. Wie geht es weiter? (Meilenstein 2, 15.10.)

* **Vorverarbeitung vergleichen:** Glättung (Savitzky-Golay), SNV-Normierung, Ableitungen
  der Spektren, Vegetationsindizes als Merkmale, Ausreißer entfernen ja/nein.
* **Modelle vergleichen:** tabellarisch (Gradient Boosting, SVM, MLP) gegen
  sequenziell (1D-CNN, GRU – das Spektrum als Kurve betrachtet).
* **Strategien vergleichen:** flach, getrennt, hierarchisch (erst Pflanze, dann Stadium),
  Multi-Task.
* **Saubere Validierung:** 5-fach stratifizierte Kreuzvalidierung, Cluster-Split als Gegenprobe.
* **Fehleranalyse:** Konfusionsmatrix, Ergebnisse je Klasse, Vergleich mit der Baseline.

---

## 12. Spickzettel: die wichtigsten Zahlen

| Was | Zahl |
|---|---|
| Trainingsproben | 5.591 (nach Duplikaten 5.589) |
| Testproben ohne Label | 1.397 |
| Bänder gesamt / leer / nutzbar | 198 / 67 / **131** |
| Fehlende Einzelwerte | 48 (in 44 Zeilen) |
| Pflanzen / Stadien / Kombinationen | 5 / 6 / **23** |
| Häufigste / seltenste Pflanze | Mais 2.097 / Reis 93 (22 : 1) |
| Kleinste Kombination | Baumwolle/Ernte, 11 Proben |
| Nur nachschlagen (AEZ + Monat) | BAcc Pflanze 0,72 / Stadium 0,65 |
| Korrelation Nachbarbänder | r = 0,999 |
| PCA | 3 Komponenten = 96 %, 10 = 99,7 % |
| Pflanze nur am Spektrum erkennbar | 90 % bei Vollbedeckung, 63 % bei Ernte |
| Ausreißer (LOF / Plausibilität / Mahalanobis) | 39 / 33 / 2.013 (Verfahren ungeeignet) |
| Train vs. Test unterscheidbar? | AUC 0,50 → nein |
| **Baseline BAcc Pflanze / Stadium / Kombi** | **0,827 / 0,829 / 0,692** |
| Baseline Samples-F1 | 0,858 |
| Baseline Cluster-Split (Kombi) | 0,390 |
| Zufallsrater (Kombi) | 0,040 |

---

## 13. Vorschlag für die Meilenstein-Präsentation

Etwa 5–7 Minuten, jede Person übernimmt einen Teil.

1. **Problem und Nutzen** (1 min) – Abschnitt 1: Was soll erkannt werden, wozu.
2. **Die Daten** (1 min) – Tabelle aus 3, Klassenverteilung (7.1), leere Bänder = Wasserdampf (7.3).
3. **Drei Kernerkenntnisse der EDA** (2 min)
   * Das Spektrum zeigt den Lebenslauf der Pflanze (7.4, Bild `eda_spectra_stage_per_crop.png`).
   * Wo Boden dominiert, sind Pflanzen kaum unterscheidbar (7.7).
   * AEZ und Monat verraten schon viel (7.2).
4. **Pre-Processing** (30 s) – die 5 Schritte aus Abschnitt 6.
5. **Baseline + Demo** (1,5 min) – `02_Baseline_Demo.ipynb` live laufen lassen (dauert
   Sekunden), Tabelle aus Abschnitt 8, Konfusionsmatrix.
6. **Ehrliche Einordnung + nächste Schritte** (1 min) – Cluster-Split (0,39),
   schwache Klassen, Plan für Meilenstein 2.

**Vorher üben:** einmal `bash scripts/run_all.sh` laufen lassen und das Demo-Notebook
öffnen, damit beim Vorführen nichts hakt.

---

## 14. Fragen, die kommen können – mit Antworten

**„Warum fehlen bei euch Bänder?“**
Die 67 Bänder sind in beiden Datensätzen komplett leer. Sie liegen auf den
Wasserdampf-Absorptionsbanden der Atmosphäre (~1130, ~1400, ~1900 nm), am
Detektorübergang und an den Rändern. Dort kommt kein Signal am Sensor an.

**„Warum Balanced Accuracy und nicht normale Accuracy?“**
Weil die Klassen sehr ungleich groß sind. Ein Modell, das immer „Mais“ sagt, hätte 37 %
Accuracy, aber nur 20 % Balanced Accuracy. Balanced Accuracy ist der Durchschnitt der
Trefferquoten aller Klassen – jede Klasse zählt gleich. Sie ist auch das Hauptkriterium
der Bewertung.

**„Was ist der Unterschied zwischen euren zwei Splits?“**
Der stratifizierte Split verteilt einzelne Proben zufällig, der Cluster-Split verteilt
ganze Gruppen sehr ähnlicher Proben (Ersatz für Felder, weil es keine Feld-IDs gibt).
Der Cluster-Split ist strenger und zeigt, wie gut das Modell auf neuen Feldern wäre.

**„Warum ist der Cluster-Split so viel schlechter?“**
Weil Nachbarpixel eines Feldes fast gleich sind. Beim Zufallssplit liegt oft ein
„Zwilling“ im Training. Das ist für den offiziellen Test nicht schlimm (der ist ebenfalls
ein Zufallsausschnitt – AUC 0,50), aber für die Praxis müssen wir das ehrlich sagen.

**„Wie habt ihr fehlende Werte behandelt?“**
67 komplett leere Bänder gelöscht; 48 einzelne Lücken je Spektrum linear zwischen den
Nachbarbändern aufgefüllt. Das nutzt die Glattheit des Spektrums und braucht keine
Information aus anderen Zeilen – kein Datenleck.

**„Warum habt ihr die Ausreißer nicht gelöscht?“**
Die markierten Spektren sind physikalisch plausibel (lückige Baumwolle, Mischpixel).
Blind löschen könnte genau die schwierigen, aber echten Fälle entfernen, die im Test
auch vorkommen. Ob Entfernen hilft, prüfen wir in Meilenstein 2.

**„Warum Random Forest?“**
Robust, ohne Tuning brauchbar, braucht keine Skalierung, kommt mit vielen korrelierten
Bändern klar und kann Klassengewichte. Als Referenzpunkt ideal.

**„Welche Klassen sind schwierig – und warum?“**
Seltene Klassen (Reis, Baumwolle/Ernte) und bodendominierte Stadien (Auflaufen, Ernte).
Dort sieht der Satellit vor allem Erde – und Erde sieht unter Mais genauso aus wie unter
Soja. Das hat schon die EDA gezeigt (Pflanze nur zu 63 % erkennbar bei Ernte).

**„Warum nehmt ihr AEZ und Monat dazu? Ist das nicht geschummelt?“**
Die Aufgabenstellung erlaubt es ausdrücklich. Es ist auch fachlich sinnvoll: Ein Landwirt
weiß ja auch, in welcher Region und Jahreszeit er ist. Wir zeigen aber zusätzlich das
Ergebnis nur mit Spektrum (0,60 Kombi-BAcc), damit man den Beitrag sieht.

**„Was ist das Business-Ziel?“**
Großflächig und automatisch wissen, welche Kultur wo wächst und wie weit sie ist – für
Ertragsprognosen, Bewässerungs- und Düngeplanung, Versicherung und Kontrolle von
Agrarförderung.

**„Was bedeutet hierarchisch bei euch?“**
Das Stadium hängt von der Pflanze ab (nur 23 von 30 Kombinationen existieren). In der
Baseline lösen wir das, indem wir die Kombination als eine Klasse vorhersagen – so
entsteht nie eine unmögliche Kombination. Echte zweistufige Modelle (erst Pflanze, dann
Stadium) vergleichen wir in Meilenstein 2.

**„Was macht ihr für Meilenstein 3 (Daten reduzieren)?“**
Die Aufgabenstellung spricht von Zeitreihen, wir haben aber ein Spektrum je Probe. Wir
planen deshalb, die Zahl der Bänder zu reduzieren (die PCA zeigt viel Doppelung) und
zu testen, wie gut z. B. ein günstiger Multispektral-Sensor mit wenigen Bändern wäre.
Das haben wir als Frage notiert.

**„Ist das reproduzierbar?“**
Ja: feste Zufallszahl (Seed 42), feste Paketversionen in `requirements.txt`, ein Befehl
(`bash scripts/run_all.sh`) erzeugt alle Abbildungen, Tabellen und Notebooks neu.
