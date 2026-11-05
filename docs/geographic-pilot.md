# Geografiskt spridningstest för Älgdata

## Syfte

Verifiera att portalens rapport 4 (Avskjutning med mål — ÄJO) kan hämtas för områden i flera län, innan fler områden läggs till i den dagliga produktionsinsamlingen.

## Urval

Workflowen väljer högst ett område per län ur den senast insamlade nationella väljarkatalogen. Standardurvalet täcker Norrbottens, Västerbottens, Jämtlands, Dalarnas, Gävleborgs och Skåne län. Endast observationer med nuvarande gränsläge väljs. Katalogen måste avse aktuell säsong. Den tidigare upptäcktslogiken valde första (äldsta) startåret och gav därför historiska fönster som 1990/1991–1999/2000 trots att 2026/2027 fanns i portalens väljare. Upptäckten väljer nu senaste aktiverade startår och senaste aktiverade slutår. Pilotworkflowen uppdaterar katalogen live för de sex länen före urvalet. Ett valfritt minsta slutår kan anges vid manuell körning. Hämtningen använder exakt katalogens start- och slutår och tvingar inte fram ett senare startår. Hörneåns ÄSO (724577) och Gräsmyrs VVO (718148) exkluderas från urvalet för att undvika att piloten blir en upprepning av befintliga identiteter.

Urvalet är en teknisk provtagning, inte en rekommendation om områdenas representativitet. Om ett län saknar aktuell kandidat redovisas det som saknat; ingen identitet gissas fram.

## Aktuell säsong och rapporteringsfördröjning

Piloten avser jaktåret 2026/2027. Jakttiderna varierar geografiskt: i Norrbotten, Västerbotten och Jämtland börjar ordinarie jakt normalt 1 september; i Skåne 8 oktober; Dalarna och Gävleborg har olika startdatum beroende på område. Lokala beslut kan också innebära uppehåll. Att ett område saknar synliga rader tidigt under säsongen är därför inte bevis för att portalhämtningen misslyckats eller att området saknar avskjutning. Fällda älgar ska rapporteras inom två veckor efter fällning, vilket också kan ge eftersläpning.

Piloten skiljer därför på:
- portalurval och rapportanrop lyckades;
- tabellen innehöll registrerade datarader;
- portalen visade ingen datarad för vald period;
- tabellstruktur kunde inte tolkas.

Tomt resultat är en giltig observation och ska inte klassas som parserfel. Det är inte heller ett bevis för noll fällda älgar. I rapport 4 heter den tredje kolumnen **Slutrapporterat** och innehåller Ja/Nej. Den är inte en jaktårskolumn; CSV-fältet normaliseras därför till `slutrapporterat`.

## Vad testet mäter

För varje kandidat:
- om län, ÄFO, gränsläge, jaktår och portal-ID kan väljas i samma offentliga portal;
- om rapport 4 ger en tabell med data;
- vilket slutår portalen faktiskt tillåter;
- antal returnerade datarader och eventuella fel.

Varje län körs separat. Ett misslyckat område hindrar inte de övriga försöken. Workflowen laddar upp en sammanfattning och varje portals diagnostik som artifact. Inga pilotuttag läggs i produktionsmappen \`data/daily_snapshots/\` eller committas automatiskt.

## Tolkningsgränser

En lyckad portalhämtning visar endast att urvalet och rapportanropet fungerade vid testtillfället. Tomma säsongstabeller måste följas upp vid senare snapshots. Den bekräftar inte permanent geografisk identitet, Excel-cellernas överensstämmelse, historiska områdesrelationer eller daglig stabilitet. Först efter analys av resultatet väljs områden för en separat, kontrollerad snapshotfas.

## CSV-fält och källrubriker

CSV-exporten följer rapportens tvådelade tabellhuvud. Tredje källkolumnen är `Slut- rapporterat` och anger om jaktområdet är slutrapporterat. Den får inte benämnas `jaktsasong`, eftersom det felaktigt antyder att Ja/Nej-värdet avser jaktsäsongens status. Jaktåret framgår i stället av uttagets metadata och filnamn.
