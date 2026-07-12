# Kanal-Radar (GitHub-Variante)

Überwacht TikTok-Profile automatisch über **GitHub Actions** und zeigt neue
Uploads über **GitHub Pages** an — kein eigener Server, kein Terminal im
Alltag nötig, komplett kostenlos.

## Wie es funktioniert

- `channels.json` — hier trägst du ein, welche Kanäle beobachtet werden sollen.
- Eine **GitHub Action** (`.github/workflows/check-channels.yml`) läuft alle
  10 Minuten automatisch, prüft die fälligen Kanäle per `yt-dlp` und schreibt
  Ergebnisse nach `data/status.json` / `data/events.json`.
- **GitHub Pages** zeigt `index.html` als Webseite an, die diese beiden
  Dateien einliest und das Dashboard mit "NEU"-Badges anzeigt.

Kein offizielles TikTok-API nötig, aber auch kein Echtzeit-Push: Die Prüfung
läuft alle ~10 Minuten (abhängig vom individuellen Intervall pro Kanal),
GitHub-Zeitpläne können zusätzlich ein paar Minuten Verzögerung haben.

## Einmalige Einrichtung (ca. 5 Minuten, alles im Browser)

### 1. Neues Repository erstellen
Auf github.com → **New repository** → Namen vergeben (z. B. `kanal-radar`)
→ **Public** wählen (wichtig: bei öffentlichen Repos sind GitHub-Actions-Minuten
unbegrenzt kostenlos; bei privaten Repos gibt es ein kostenloses Monatslimit,
das für dieses Projekt i. d. R. aber auch reicht).

### 2. Diese Dateien hochladen
Im neuen Repo: **Add file → Upload files** → alle Dateien aus diesem Ordner
(inkl. der Unterordner `.github/`, `data/`, `scripts/`) per Drag & Drop
hochladen → **Commit changes**.

*Tipp:* Falls der Upload-Dialog versteckte Ordner wie `.github` nicht per
Drag&Drop annimmt, nutze stattdessen `git`:
```bash
cd kanal-radar-github
git init
git add .
git commit -m "Initial"
git branch -M main
git remote add origin https://github.com/DEIN-NAME/kanal-radar.git
git push -u origin main
```

### 3. Actions Schreibrechte aktivieren
Repo → **Settings → Actions → General → Workflow permissions** →
**Read and write permissions** auswählen → **Save**.
(Ohne das kann die Action ihre Ergebnisse nicht zurück ins Repo committen.)

### 4. GitHub Pages aktivieren
Repo → **Settings → Pages** → unter **Build and deployment**:
Source = **Deploy from a branch**, Branch = **main**, Ordner = **/ (root)**
→ **Save**. Nach ca. 1 Minute ist das Dashboard erreichbar unter:
```
https://DEIN-NAME.github.io/kanal-radar/
```

### 5. Ersten Check manuell auslösen
Repo → Tab **Actions** → Workflow **"Kanäle prüfen"** → **Run workflow** →
**Run workflow** bestätigen. Nach ca. 30–60 Sekunden sind `data/status.json`
und `data/events.json` aktualisiert, das Dashboard zeigt die Ergebnisse.

## Kanäle verwalten

`channels.json` im Repo öffnen (Stift-Symbol = bearbeiten), Eintrag
hinzufügen/entfernen, z. B.:

```json
[
  { "username": "nasa", "profile_url": "https://www.tiktok.com/@nasa", "interval_minutes": 20 },
  { "username": "beispiel", "profile_url": "https://www.tiktok.com/@beispiel", "interval_minutes": 30 }
]
```

Speichern (**Commit changes**) — beim nächsten Actions-Lauf wird der neue
Kanal automatisch mit aufgenommen. Kein Terminal nötig.

## Hinweise

- **Intervall:** mindestens 10–15 Minuten empfohlen, um TikTok nicht zu
  provozieren. Bei sehr vielen Kanälen eher 20–30 Minuten.
- **`yt-dlp`-Updates:** Der Workflow installiert bei jedem Lauf automatisch
  die neueste `yt-dlp`-Version (`pip install -U yt-dlp`), das hält es
  robust gegen TikTok-Änderungen — ohne dass du etwas tun musst.
- **Nutzungsbedingungen:** Automatisiertes Abrufen von TikTok-Inhalten kann
  gegen TikToks Nutzungsbedingungen verstoßen. Für eigenes Monitoring/
  Recherche gedacht, nicht für Massen-Scraping.
- **Fehlerstatus:** Hängt ein Kanal dauerhaft auf "error", meist weil das
  Profil privat/gelöscht ist oder TikTok blockt — Fehlermeldung erscheint
  direkt in der Kanalkarte im Dashboard.

## Lokal testen (optional)

```bash
pip install yt-dlp
python3 scripts/run_checks.py
```
Prüft alle fälligen Kanäle aus `channels.json` und aktualisiert die
`data/*.json`-Dateien lokal.
