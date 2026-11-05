# Geografiskt spridningstest för Älgdata

## Syfte

Verifiera att portalens rapport 4 (Avskjutning med mål — ÄJO) kan hämtas för områden i flera län, innan fler områden läggs till i den dagliga produktionsinsamlingen.

## Urval

Workflowen väljer högst ett område per län ur den senast insamlade nationella väljarkatalogen. Standardurvalet täcker Norrbottens, Västerbottens, Jämtlands, Dalarnas, Gävleborgs och Skåne län. Endast observationer med nuvarande gränsläge och katalogiserat slutår från 2024/2025 eller senare väljs. Hörneåns ÄSO (724577) och Gräsmyrs VVO (718148) exkluderas från urvalet för att undvika att piloten blir en upprepning av befintliga identiteter.

Urvalet är en teknisk provtagning, inte en rekommendation om områdenas representativitet. Om ett län saknar aktuell kandidat redovisas det som saknat; ingen identitet gissas fram.

## Vad testet mäter

För varje kandidat:
- om län, ÄFO, gränsläge, jaktår och portal-ID kan väljas i samma offentliga portal;
- om rapport 4 ger en tabell med data;
- vilket slutår portalen faktiskt tillåter;
- antal returnerade datarader och eventuella fel.

Varje län körs separat. Ett misslyckat område hindrar inte de övriga försöken. Workflowen laddar upp en sammanfattning och varje portals diagnostik som artifact. Inga pilotuttag läggs i produktionsmappen \`data/daily_snapshots/\` eller committas automatiskt.

## Tolkningsgränser

En lyckad hämtning visar endast att en rapport kunde hämtas vid testtillfället. Den bekräftar inte permanent geografisk identitet, Excel-cellernas överensstämmelse, historiska områdesrelationer eller daglig stabilitet. Först efter analys av resultatet väljs områden för en separat, kontrollerad snapshotfas.
