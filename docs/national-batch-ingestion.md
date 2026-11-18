# Nationell Älgdata – batchad och återupptagningsbar insamling

## Status och säkerhetsgräns

Detta dokument beskriver målarkitekturen för nationell insamling efter godkänt femområdesprov (#3). Den första implementationen lägger till deterministisk batchplanering och ett versionshanterat checkpoint-manifest.

**Detta steg aktiverar inte nationell produktion.** Befintlig regional daglig insamling lämnas oförändrad. Batchmanifestet anger uttryckligen `production_write=false`. Inga nya portalhämtningar eller publiceringar till webbplatsen sker genom batchmodulen i detta steg.

## Vad preflight #3 visade

- 626 av 626 valda områden kunde väljas i portalen.
- 619 rapporter hade datarader och 7 saknade redovisade rader.
- Inga tekniska fel registrerades.
- Portalhämtningen tog ungefär 78 minuter för 626 områden, cirka 7,5 sekunder per område i genomsnitt.
- Katalogen innehöll 3 236 unika aktuella områden vid den körningen. En rent linjär uppskattning för alla dessa är cirka 6 timmar och 45 minuter, exklusive overhead och avvikelser.
- Gotlands län ingår inte i Älgdatas länsväljare. Det är förväntat: enligt verksamhetsinformationen saknar Gotland älgstam/älgförvaltning. Sverige har 21 administrativa län men Älgdatas relevanta länstäckning är 20. Gotland redovisas som ett uttryckligt undantag, inte som en datalucka.

## Målflöde

1. Uppdatera den nationella väljarkatalogen.
2. Skapa en fast kandidatlista för en viss körning, jaktår, rapport och gränsläge.
3. Dela kandidatlistan deterministiskt i batchar (initialt 100 områden).
4. Hämta områden sekventiellt inom batchen med den befintliga, verifierade nedladdaren.
5. Spara varje områdesresultat och uppdatera checkpoint-manifestet atomiskt.
6. Vid avbrott återupptas körningen från första batch/område som saknar ett slutligt resultat.
7. Publicera endast validerade och oföränderliga batchresultat till en separat webbdatakälla.
8. Bygg en nationell statusfil och slutlig sammanställning.

## Statusmodell

Områdesstatusar:
- `success`: portalvalidering lyckades och rapporten innehåller data.
- `no_data`: portalvalidering lyckades men rapporten saknar datarader. Detta får aldrig omvandlas till noll avskjutning.
- `failed`: portalvalideringen eller hämtningen misslyckades.

Batchstatusar:
- `pending`: inga resultat registrerade.
- `running`: minst ett men inte alla områdesresultat finns.
- `completed`: alla områden har slutstatus och inga tekniska fel finns.
- `completed_with_errors`: alla områden har slutstatus men minst ett tekniskt fel finns.

Ett resultat för ett okänt områdes-ID avvisas. Resultat kopplas alltid till den frysta kandidatlistan för körningen. En senare misslyckad omkörning får inte tyst ersätta ett tidigare giltigt resultat; retry-policy och versionshantering för omhämtning ska definieras i runner-steget.

## Checkpoint och publicering

`scripts/national_batching.py` innehåller rena funktioner för:
- deterministisk batchplanering;
- skapande och validering av manifest;
- klassificering av resultat;
- uppdatering av batch- och körningsstatus;
- val av nästa ofärdiga batch;
- atomisk skrivning av checkpoint;
- generering av ett kompakt publikt statusobjekt.

Nästa implementation ska lägga till en runner som anropar dessa funktioner efter varje områdeshämtning, inte bara efter varje batch. Därmed förloras högst ett pågående områdesarbete vid avbrott.

Webbpublicering ska vara separat från insamlingsprocessen. Första publicerade versionen ska endast innehålla status och batchmetadata. Rådata publiceras inte förrän datamodell, licensvillkor, cache och webbplatsens läsflöde har verifierats. Batchfiler ska vara immutabla och publiceras först efter validering.

## GitHub Actions-upplägg

- En enskild runner hålls under GitHub-hostad jobbtidsgräns.
- Flera batchjobb kan köras sekventiellt i ett workflow.
- Portalhämtningen förblir sekventiell för att inte belasta källan.
- Jobbresultat och checkpoint överförs explicit mellan jobb; lokalt runner-diskutrymme får inte betraktas som beständig lagring.
- Återupptagning över separata workflow-körningar kräver en beständig checkpoint-/batchlagring och verifiering av dess integritet.
- Workflow ska ha concurrency-skydd så att två nationella insamlingar inte körs samtidigt.

## Första batch-runnern

`scripts/run_national_batches.py` återanvänder `scripts/download_statistics.py` och kör en områdeshämtning i taget. Den läser kandidatlistan från preflightens `selected_candidates.json` (fältet `candidates`) eller från en fristående JSON-array.

Exempel på en begränsad testkörning:

```bash
python scripts/run_national_batches.py \\
  --candidates out/national-preflight/selected_candidates.json \\
  --out out/national-batch-test \\
  --batch-size 10 \\
  --area-timeout 240 \\
  --limit 10
```

Körningen skapar `manifest.json` och `areas/<area_id>/` med nedladdningsrapport, CSV och körloggar. Manifestet skrivs atomiskt efter varje områdesförsök. Om processen startas igen med samma `--out` och exakt samma kandidatlista hoppas redan slutligt klassificerade områden över. Om kandidatlistan har ändrats avbryts återupptagningen; använd då en ny utdatakatalog.

Denna första version gör inte automatiska retries av områden med status `failed`; de ligger kvar som synliga fel och retry-policy läggs till efter att grundläggande återupptagning har verifierats. `--limit` gör det möjligt att simulera avbrott utan att ändra kandidatlistan.

## Nästa utvecklingssteg

1. Köra en 10-områdes testinsamling med `--limit 10` och därefter återuppta samma körning.
2. Verifiera att färdiga områden inte hämtas igen och att checkpointen överlever en ny process.
3. Lägga till explicit retry-policy för tekniska fel och idempotent hantering av befintliga resultat.
4. Lägga till ett separat manuellt workflow för små batchar utan produktionsskrivning.
5. Verifiera beständig lagring av checkpoint och batchfiler mellan GitHub Actions-jobb.
6. Implementera webbpublicering först efter godkänt batchtest och fortsatt behandla Gotland som ett dokumenterat undantag.
