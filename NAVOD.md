# 📈 AI Akcie Analyzer – Kompletní návod zprovoznění

## Co budeš mít na konci
Lokální webová aplikace v prohlížeči, kde napíšeš přirozenou větou
*„Analyzuj GDX za posledních 200 dní"* a dostaneš graf + AI analýzu.

---

## KROK 1 – Instalace Pythonu

### Windows
1. Jdi na **https://www.python.org/downloads/**
2. Stáhni **Python 3.11** nebo novější (tlačítko „Download Python 3.x.x")
3. Spusť instalátor
4. ⚠️ **DŮLEŽITÉ:** Zaškrtni „Add Python to PATH" (dole v instalátoru!)
5. Klikni „Install Now"
6. Ověř instalaci – otevři **Příkazový řádek** (Win+R → napište `cmd` → Enter):
   ```
   python --version
   ```
   Mělo by se zobrazit: `Python 3.11.x`

### macOS
1. Otevři **Terminál** (Cmd+Space → „Terminal")
2. Nainstaluj přes Homebrew:
   ```bash
   brew install python@3.11
   ```
   Nebo stáhni instalátor z python.org stejně jako na Windows.

### Linux (Ubuntu/Debian)
```bash
sudo apt update && sudo apt install python3.11 python3-pip python3-venv -y
```

---

## KROK 2 – Stažení souborů aplikace

Vytvoř složku pro projekt, např. `C:\akcie_analyzer\` (Windows)
nebo `~/akcie_analyzer/` (Mac/Linux).

Do ní ulož oba soubory, které jsi dostal od Claudea:
```
akcie_analyzer/
├── akcie_analyzer.py     ← hlavní aplikace
└── requirements.txt      ← seznam knihoven
```

---

## KROK 3 – Vytvoření virtuálního prostředí

Virtuální prostředí = izolovaný Python pro tento projekt (neovlivní zbytek systému).

Otevři terminál / příkazový řádek a přejdi do složky:

```bash
# Windows
cd C:\akcie_analyzer

# Mac/Linux
cd ~/akcie_analyzer
```

Vytvoř virtuální prostředí:
```bash
python -m venv venv
```

Aktivuj ho:
```bash
# Windows (Příkazový řádek)
venv\Scripts\activate

# Windows (PowerShell)
venv\Scripts\Activate.ps1

# Mac/Linux
source venv/bin/activate
```

Poznáš, že je aktivní – v terminálu uvidíš `(venv)` na začátku řádku.

---

## KROK 4 – Instalace knihoven

S aktivním virtuálním prostředím spusť:
```bash
pip install -r requirements.txt
```

Instalace trvá 1–3 minuty. Na konci by mělo být:
`Successfully installed streamlit yfinance anthropic plotly ...`

---

## KROK 5 – Získání Claude API klíče

1. Jdi na **https://console.anthropic.com/**
2. Zaregistruj se (nebo přihlas)
3. V levém menu klikni na **„API Keys"**
4. Klikni **„Create Key"**
5. Zkopíruj klíč – začíná `sk-ant-...`
6. ⚠️ Klíč se zobrazí jen jednou – ulož si ho!

**Cena:** Anthropic nabízí kredit zdarma pro nové účty.
Analýza jednoho tickeru stojí přibližně $0.002–0.005 (zlomky centů).

---

## KROK 6 – Spuštění aplikace

S aktivním virtuálním prostředím ve složce projektu:
```bash
streamlit run akcie_analyzer.py
```

Terminál vypíše:
```
  You can now view your Streamlit app in your browser.
  Local URL: http://localhost:8501
```

Prohlížeč se otevře automaticky. Pokud ne, otevři ručně:
**http://localhost:8501**

---

## KROK 7 – Použití aplikace

1. **Vlevo v panelu** vlož svůj Claude API klíč (pole „Claude API klíč")
2. Do pole nahoře napiš dotaz, např.:
   - `Analyzuj GDX za posledních 200 dní`
   - `Jak si vede NVDA za 100 dní?`
   - `Volatilita a trend SPY 150 dní`
3. Klikni **▶ Analyzovat**
4. Počkej 10–20 sekund → zobrazí se graf, metriky a AI analýza

---

## Každodenní spuštění (od druhého dne)

```bash
# 1. Přejdi do složky
cd C:\akcie_analyzer       # Windows
cd ~/akcie_analyzer        # Mac/Linux

# 2. Aktivuj prostředí
venv\Scripts\activate      # Windows
source venv/bin/activate   # Mac/Linux

# 3. Spusť
streamlit run akcie_analyzer.py
```

**Tip pro Windows:** Vytvoř si soubor `spustit.bat` ve složce:
```bat
@echo off
call venv\Scripts\activate
streamlit run akcie_analyzer.py
```
Pak stačí dvojkliknout na `spustit.bat`.

---

## Řešení problémů

| Problém | Řešení |
|---|---|
| `python` není rozpoznán | Přeinstaluj Python se zaškrtnutým „Add to PATH" |
| `ModuleNotFoundError` | Zkontroluj, že je aktivní `(venv)` a spusť `pip install -r requirements.txt` |
| Neplatný API klíč | Zkontroluj na console.anthropic.com, klíč začíná `sk-ant-` |
| Prázdná data pro ticker | Zkontroluj přesný symbol (např. `CEZ.PR` pro ČEZ na pražské burze) |
| Port 8501 obsazený | Spusť `streamlit run akcie_analyzer.py --server.port 8502` |

---

## Podporované tickery (příklady)

| Co chceš | Ticker |
|---|---|
| Gold Miners ETF | GDX |
| S&P 500 | SPY |
| Nasdaq 100 | QQQ |
| Gold | GLD |
| Apple | AAPL |
| Tesla | TSLA |
| Nvidia | NVDA |
| Bitcoin ETF | IBIT |
| ČEZ (Praha) | CEZ.PR |

Data jsou se zpožděním ~15 minut (Yahoo Finance zdarma).

---

*Aplikace vytvořena s pomocí Claude (Anthropic) · Data: Yahoo Finance*
