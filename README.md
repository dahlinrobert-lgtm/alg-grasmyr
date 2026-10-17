# Älgdata – Gräsmyr och Hörneåns älgskötselområde

Projekt för att samla in, versionshantera och analysera älgstatistik med fokus på **Gräsmyrs viltvårdsområde (historisk områdesidentitet)** och **Hörneåns älgskötselområde (nuvarande förvaltningsområde)**.

## Datakällor

- [Länsstyrelsernas statistikportal Älgdata](https://algdata-apps.lansstyrelsen.se/algdata-apps-stat/)
- [Länsstyrelsens Älgdata WebbGIS](https://ext-webbgis.lansstyrelsen.se/lst_algdata/)
- [Älgdata – översikt och information](https://www.algdata.se/)
- [Älgdata – statistikens startsida och vägledning](https://www.algdata.se/statistik/)

Statistikportalen har diagram/tabeller och stöd för export till bland annat Excel. Den beskriver statistik om avskjutning, slaktvikter, viltolyckor, älgobservationer och biologiska uppgifter. WebbGIS kan användas för att kontrollera områdesnamn, ID och gränser.

## Viktigt om geografisk jämförbarhet

Gräsmyrs viltvårdsområde och Hörneåns älgskötselområde ska tills vidare behandlas som **två separata områdesidentiteter**. Älgdata skiljer mellan jaktområden (till exempel licensområden) och älgskötselområden. Ett äldre område kan ha ingått i eller motsvaras av endast en del av ett senare område. Jämför inte deras råa totalsiffror som om geografin vore oförändrad innan officiella ID:n och historiska gränser har kontrollerats.

## Prioriterad inhämtning

1. **Avskjutning** – antal fällda älgar, uppdelat efter de dimensioner som faktiskt finns i exporten.
2. **Älgobservationer (älgobs)** – observerade älgar och relevanta mått enligt källans definitioner.
3. **Slaktvikter/kalvvikter** – när antal observationer och viktdefinitioner framgår.
4. **Övriga tillgängliga kategorier** – biologiska data, viltolyckor och andra relevanta indikatorer, med tydlig notering om geografisk nivå.

Börja med en export för Hörneåns ÄSO och en separat export för historiska Gräsmyrs VVO. Ta med så många jaktår som portalen erbjuder och upprepa för varje statistiktyp.

## Kom igång

Se [guide för datahämtning](docs/acquisition.md).

När en Excel-export har laddats ned kan den granskas utan att anta att kolumnerna redan är kända:

```bash
python -m pip install -r requirements.txt
python scripts/inspect_export.py path/to/export.xlsx
python scripts/prepare_export.py path/to/export.xlsx --out data/processed
```

Skriptet förbereder CSV-kopior per kalkylblad och en manifestfil; det bevarar värdena från exporten men gör inte ännu någon källspecifik tolkning av statistikvariabler. En riktig export måste granskas innan en pålitlig normalisering och helt automatiserad hämtning kan implementeras.

## Projektstruktur

```
data/
  raw/                 # oförändrade exporter från Älgdata
  processed/           # CSV-kopior och senare standardiserade tabeller
docs/
  acquisition.md       # steg-för-steg för datainsamling
  data-dictionary.md   # preliminärt schema och kvalitetsregler
scripts/
  inspect_export.py    # inspekterar exempel på exportfiler
  prepare_export.py    # CSV-kopior + manifest från xlsx
  inspect_portal.py    # kontrollerar publika fält, områden och endpoints
  download_statistics.py # hämtar en Excel-rapport via statistikportalen
```

## Status

- [x] Identifierat statistikportalen och WebbGIS som relevanta primärkällor.
- [x] Lagt till verktyg för att inspektera och förbereda exporter.
- [x] Identifierat Hörneåns ÄSO i statistikportalens områdeslista: `24-01-02-342-Ä`, portal-ID `724577`, under Sydöstra ÄFO.
- [x] Identifierat Gräsmyrs VVO i statistikportalens områdeslista: `24-01-02-017-A`, portal-ID `718148`, också under Sydöstra ÄFO.
- [ ] Verifiera det historiska ID:t och gränserna för Gräsmyrs viltvårdsområde.
- [ ] Kontrollera utfallet från första automatiserade Excel-exporten i GitHub Actions och spara en verifierad råexport.
- [ ] Mappa exporternas verkliga kolumner till ett stabilt schema.
- [ ] Undersöka statistikportalens faktiska nätverksanrop/exportväg innan eventuell schemalagd automatisering byggs.

## Källhantering

Behåll alltid originalexporterna, notera hämtningstidpunkt och valda filter, dokumentera definitioner och följ Länsstyrelsens villkor för återanvändning. Saknade värden ska inte ersättas med noll. Jaktår ska behållas i källans format tills formatet är verifierat.
