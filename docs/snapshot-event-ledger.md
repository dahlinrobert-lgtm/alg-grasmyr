# Snapshot-händelselogg och källverifiering

## Syfte och avgränsning

Händelseloggen byggs från intilliggande dagliga portaluttag under \`data/daily_snapshots/\`. Den beskriver observerade skillnader mellan två snapshots för samma område och jaktår. Den är inte en logg över exakta händelsedatum i fält.

## Händelsetyper

- \`reported_value_increase\`: ett numeriskt kumulativt avskjutningsfält har ökat. Tolkning: nyregistrerad rapportering i portalen, inte ett säkert fälldatum.
- \`new_value\`: tomt fält har fått ett värde.
- \`value_removed\`: tidigare värde saknas i senare snapshot; inte automatiskt noll.
- \`correction\`: ett värde har ändrats på annat sätt eller minskat; orsaken kan inte fastställas från snapshots ensamma.
- \`new_season\`: jaktår tillkommer i portaluttaget.
- \`season_missing\`: jaktår saknas i senare portaluttag; kan bero på urval eller publicering och är inte bevis för att historik raderats.

Oförändrade fält skapar inga händelser.

## Utdata

- \`data/events/<area>_events.jsonl\`: maskinläsbar, en händelse per rad.
- \`data/events/<area>_events.csv\`: semikolonseparerad tabell.
- \`data/quality/snapshot_quality_report.json\`: täckning, snapshot- och händelseantal samt inventering av Excel-kandidater.

Händelse-ID beräknas deterministiskt från område, snapshotdatum, jaktår, fält, klassificering och gamla/nya värden. Samma indata ger samma ID och samma logg.

## Primärkälla: myndighetens Excel-exporter

Projektets källhierarki anger publicerade Excel-exporter som primärkälla. Den automatiska inventeringen listar Excel-filer under \`data/raw/\`, men gör ingen automatisk källmatchning. En fil är inte en verifierad källa enbart för att filnamnet verkar relevant. För automatisk avstämning ska ett separat manifest ange minst fil, område/portal-ID, jaktår, gränsläge och exportens kontrollsumma. Saknade eller oklara matchningar ska redovisas som ej verifierade, aldrig som godkända.
