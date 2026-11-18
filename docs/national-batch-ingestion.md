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

## Nästa utvecklingssteg

1. Implementera en sekventiell batch-runner med checkpoint efter varje område.
2. Lägg till tester för avbrott, återupptagning, retry och idempotent publicering.
3. Lägg till ett separat manuellt testworkflow som kör en liten batch utan produktionsskrivning.
4. Verifiera hur checkpoint och batchfiler ska lagras beständigt.
5. Implementera webbpublicering först efter godkänt batchtest.
6. Kör en full nationell testinsamling utan produktionsskrivning och behandla Gotland som ett dokumenterat undantag.
