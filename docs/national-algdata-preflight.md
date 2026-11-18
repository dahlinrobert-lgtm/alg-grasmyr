# Nationell Älgdata – teknisk förkontroll

## Syfte och säkerhetsgräns

Den nationella förkontrollen verifierar att rapport 4 (Avskjutning med mål — ÄJO) kan hämtas för aktuella jaktområden i samtliga ÄFO som finns i den nationella väljarkatalogen. Den är en teknisk provkörning, inte produktionsinsamling.

**Förkontrollen skriver aldrig till dagliga snapshots, regional pilot-historik eller produktionsdata.** Resultat och råa diagnostikfiler sparas endast som GitHub Actions-artifact i 30 dagar.

## Urval

- Katalogen uppdateras live från den publika portalen innan provhämtningen.
- Endast `boundary_mode=current` används.
- Endast katalograder med slutår minst det begärda jaktåret väljs.
- Standard är fem jaktområden per ÄFO. Urvalet sprids jämnt över den sorterade listan av områden i respektive AFO, så att provet inte bara tar de första alfabetiska posterna.
- Sverige har 21 administrativa län, men Älgdatas relevanta länstäckning är 20. Gotlands län är uttryckligen undantaget eftersom det saknar älgstam/älgförvaltning och inte finns i statistikens länsväljare. Det räknas inte som en saknad datakälla. Saknas något av de övriga 20 länen rapporteras det som upptäcktsavvikelse.
- Kända pilotidentiteter 724577 (Hörneåns ÄSO) och 718148 (Gräsmyrs VVO) hoppas över för att undvika dubbelinsamling.
- Portal-ID behandlas som en observerad källnyckel, inte som permanent geografisk identitet.
- Katalogens ålder kontrolleras; äldre än 14 dagar stoppar provhämtningen.

## Körning

Workflow: `National Älgdata preflight` (manuell `workflow_dispatch`).

Standardinställningar:
- jaktår: minst 2026/2027;
- fem områden per aktuellt ÄFO (kan ändras via workflow-input);
- rapport-ID 4;
- högst 240 minuter för hela körningen.

Varje område hämtas separat och sekventiellt genom den befintliga `download_statistics.py` för att undvika onödig belastning på portalen. Ett enskilt områdes timeout eller portalproblem registreras som fel och hindrar inte att senare områden provas. Varje anrop har 180 sekunders timeout. Fem områden per AFO ger cirka 626 prov i den katalog som granskades 2026-11-18; faktisk mängd beräknas om från den nya livekatalogen vid varje körning.

## Resultat och tolkning

Artifact innehåller:
- `selected_candidates.json`: valda områden och täckning per län/ÄFO, inklusive länsrevision, saknade län och uttryckliga undantag;
- `national_preflight_summary.json`: resultat per område och total summering;
- en katalog per område med `download-report.json` och eventuell CSV.

Status skiljer mellan lyckad portalhämtning, tillgängliga datarader, tom rapport och fel. En tom tabell betyder inte noll fällda älgar. Ändringar i kumulativa avskjutningsvärden ska inte tolkas som exakta fälldatum.

## Kriterier före full nationell provtagning

1. Alla aktuella län och ÄFO i katalogen finns med i urvalsrapporten, med undantag som redovisas explicit.
2. Portal-ID, län, ÄFO, jaktår och gränsläge matchar mellan katalog och portalrapport.
3. Tomma tabeller är åtskilda från tekniska fel.
4. Misslyckade hämtningar har diagnostik och påverkar inte identiteten för andra områden.
5. Femområdesprovet granskas innan provet utökas till samtliga cirka 3 200 områden.
6. Avvikande täckning bland de 20 relevanta länen utreds separat; Gotland redovisas som ett känt undantag.

Ingen daglig nationell workflow eller produktionsarkivering aktiveras av detta steg.
