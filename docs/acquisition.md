# Datahämtning från Älgdata

## Varför exportbaserat första steg?

Statistikportalen bekräftar att resultat kan exporteras till Excel, men projektet har ännu inte verifierat något dokumenterat, stabilt publikt API för all statistik. Därför börjar projektet med riktiga exporter från portalen och undersöker därefter om samma data kan hämtas automatiskt via en stabil endpoint. Bygg inte en scraper mot gissade URL:er.

## Första export: Hörneåns älgskötselområde

1. Öppna [Statistik Älgdata](https://algdata-apps.lansstyrelsen.se/algdata-apps-stat/).
2. Välj statistiktyp, med **Avskjutning** som första test.
3. Välj **Västerbottens län**, relevant ÄFO, jaktår från/till och **Hörneåns älgskötselområde** som jaktområde om det finns i urvalslistan.
4. Kontrollera att tabell/diagram visar det valda området och rätt period. Portalen visar statistiktyperna i sin vänstermeny och har exportfunktion.
5. Exportera resultatet till Excel. Exportera varje statistiktyp separat.
6. Lägg originalfilen under `data/raw/<statistiktyp>/`, exempelvis `data/raw/avskjutning/horneans_aso_2010-2025.xlsx`.
7. Spara den exakta portaladressen, valda filter, tidpunkt för export och eventuell skärmbild i filens metadata/noteringar.
8. Kör `python scripts/inspect_export.py <fil>` och granska bladnamn, kolumnrubriker och urvalsrader.

## Historisk export: Gräsmyrs viltvårdsområde

Upprepa flödet separat för det historiska namnet/området. Om urvalet har ett alternativ för historiska gränser, testa både historiska och nuvarande gränser och dokumentera vilket som används. Om Gräsmyrs VVO inte går att välja, använd WebbGIS för att leta efter tidigare namn och områdes-ID och kontakta Länsstyrelsen vid oklarhet.

**Viktigt:** Gräsmyrs VVO ska inte automatiskt behandlas som identiskt med hela Hörneåns ÄSO. Verifiera områdestyp, ID, areal och geometri innan du kedjar ihop deras tidsserier. Lagra även källans områdesnamn exakt som det visas.

## Första statistikpaket

Ta helst ut samma jaktårsintervall för båda områdesidentiteterna:
- Avskjutning
- Älgobservationer (älgobs)
- Slaktvikter/kalvvikter om de finns för området
- Biologiska uppgifter om de finns och har tillräcklig täckning

Lägg till fler statistiktyper först när exportens geografi, definitioner och täckning är förstådda.

## Förbereda exporten

Installera beroendet:

```bash
python -m pip install -r requirements.txt
```

Inspektera filen och skapa CSV-kopior:

```bash
python scripts/inspect_export.py data/raw/avskjutning/fil.xlsx
python scripts/prepare_export.py data/raw/avskjutning/fil.xlsx --out data/processed
```

CSV-kopiorna är fortfarande källtrogna rad-/bladkopior, inte en statistiskt normaliserad tabell. När en verklig export finns i projektet ska en källa-specifik mappning byggas utifrån faktiska rubriker och definitioner.

## Automatiserad nedladdning

Workflowet [Download expanded Älgdata history](../.github/workflows/download-expanded-history.yml) kan startas från fliken **Actions** eller köras månadsvis. Det försöker hämta:
- Hörneåns ÄSO: 2010/2011–2019/2020 med historiska gränser och 2020/2021–2025/2026 med nuvarande gränser.
- Gräsmyrs VVO: 2010/2011–2019/2020 med historiska gränser samt ett separat försök för 2020/2021–2025/2026.
- Vid manuell körning kan workflowet även försöka rapporterna medelålder (rapport 9), slaktvikt (rapport 20) och älgobservationer (rapport 25).

Råa CSV-utdrag och `download-report.json` ligger i GitHub Actions-artifacts, inte i repots versionshanterade `data/processed`. Granska rapportens valda områdes-ID, jaktår, fel och tabellrader innan du för över något till analysfilerna. Vissa statistiktyper eller äldre områden kan sakna täckning; det ska registreras som saknad data, inte noll.

## Automatisering – beslutskriterier

Automatisera hämtningen först när alla punkter nedan är uppfyllda:
- exportens format och metadata är kända;
- en stabil offentlig endpoint eller en reproducerbar exportväg har identifierats;
- området och jaktårsfiltren matchar det manuella resultatet;
- scriptet kan upptäcka tomt resultat och ändrade svarsfält;
- hämtning loggas och rådata sparas utan att skrivas över;
- återanvändningsvillkor för data och kartlager är kontrollerade.
