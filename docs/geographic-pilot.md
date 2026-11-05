# Geografiskt spridningstest för Älgdata

## Syfte

Verifiera att portalens rapport 4 (Avskjutning med mål — ÄJO) kan hämtas för områden i flera län, innan fler områden läggs till i den dagliga produktionsinsamlingen.

## Urval

Workflowen väljer som standard högst fem områden per län ur den senast insamlade väljarkatalogen. Standardurvalet täcker Norrbottens, Västerbottens, Jämtlands, Dalarnas, Gävleborgs och Skåne län, alltså upp till 30 områden. Urvalet sprids över olika ÄFO först (ett område per ÄFO innan ett andra område väljs från samma ÄFO). Antalet kan ändras vid manuell körning. Endast observationer med nuvarande gränsläge väljs. Katalogen måste avse aktuell säsong. Den tidigare upptäcktslogiken valde första (äldsta) startåret och gav därför historiska fönster som 1990/1991–1999/2000 trots att 2026/2027 fanns i portalens väljare. Upptäckten väljer nu senaste aktiverade startår och senaste aktiverade slutår. Pilotworkflowen uppdaterar katalogen live för de sex länen före urvalet. Ett minsta slutår kan anges; standardvärdet är 2026, vilket begränsar piloten till jaktåret 2026/2027. Äldre år ska bara tas med när en separat historisk pilot uttryckligen efterfrågas. Hämtningen använder exakt katalogens start- och slutår och tvingar inte fram ett senare startår. Hörneåns ÄSO (724577) och Gräsmyrs VVO (718148) exkluderas från urvalet för att undvika att piloten blir en upprepning av befintliga identiteter.

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
- län, ÄFO och antal valda områden per län;
- spridning över ÄFO inom respektive län;
- om län, ÄFO, gränsläge, jaktår och portal-ID kan väljas i samma offentliga portal;
- om rapport 4 ger en tabell med data;
- vilket slutår portalen faktiskt tillåter;
- antal returnerade datarader och eventuella fel.

Varje län körs separat. Ett misslyckat område hindrar inte de övriga försöken. Workflowen laddar upp en sammanfattning och varje portals diagnostik som artifact. Inga pilotuttag läggs i produktionsmappen \`data/daily_snapshots/\` eller committas automatiskt.

## Tolkningsgränser

En lyckad portalhämtning visar endast att urvalet och rapportanropet fungerade vid testtillfället. Tomma säsongstabeller måste följas upp vid senare snapshots. Den bekräftar inte permanent geografisk identitet, Excel-cellernas överensstämmelse, historiska områdesrelationer eller daglig stabilitet. Först efter analys av resultatet väljs områden för en separat, kontrollerad snapshotfas.

## CSV-fält och källrubriker

CSV-exporten följer rapportens tvådelade tabellhuvud. Tredje källkolumnen är `Slut- rapporterat` och anger om jaktområdet är slutrapporterat. Den får inte benämnas `jaktsasong`, eftersom det felaktigt antyder att Ja/Nej-värdet avser jaktsäsongens status. Jaktåret framgår i stället av uttagets metadata och filnamn.

## Flerområdesurval och täckning

Standardpiloten väljer högst fem områden per län och prioriterar geografisk/organisatorisk spridning genom att gå igenom ÄFO i rundor. Först väljs ett område från varje ÄFO, därefter ett andra område från respektive ÄFO och så vidare. Portal-ID:n dedupliceras inom katalogurvalet och får inte tilldelas flera län. Om samma ID förekommer i flera län registreras kollisionen och den andra förekomsten hoppas över. Sammanfattningen redovisar antal valda områden och antal unika ÄFO per län, saknade län, ID-kollisioner, portalframgångar, datarader och fel.

Ett område som saknas efter urvalet betyder att katalogen inte hade tillräckligt många kandidater som uppfyllde säsongs- och identitetsfiltren; det är inte bevis för att länet saknar jaktområden. Pilotresultaten lagras som workflow-artefakt och förs inte automatiskt in i produktionshistoriken.
