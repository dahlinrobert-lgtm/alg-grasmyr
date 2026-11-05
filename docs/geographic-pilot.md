# Geografiskt spridningstest för Älgdata

## Syfte

Verifiera att portalens rapport 4 (Avskjutning med mål — ÄJO) kan hämtas för områden i flera län, innan fler områden läggs till i den dagliga produktionsinsamlingen.

## Urval

Workflowen väljer högst ett område per län ur den senast insamlade nationella väljarkatalogen. Standardurvalet täcker Norrbottens, Västerbottens, Jämtlands, Dalarnas, Gävleborgs och Skåne län. Endast observationer med nuvarande gränsläge väljs. Katalogen innehåller områden med olika historiska tidsintervall; urvalet väljer därför den senaste tillgängliga perioden per län utan att kräva att alla områden har data till 2024/2025. Ett valfritt minsta slutår kan anges vid manuell körning. Hämtningen använder exakt katalogens start- och slutår och tvingar inte fram ett senare startår. Hörneåns ÄSO (724577) och Gräsmyrs VVO (718148) exkluderas från urvalet för att undvika att piloten blir en upprepning av befintliga identiteter.

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
