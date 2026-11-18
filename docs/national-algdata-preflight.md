# Nationell Älgdata – teknisk förkontroll

## Syfte och säkerhetsgräns

Den nationella förkontrollen verifierar att rapport 4 (Avskjutning med mål — ÄJO) kan hämtas för aktuella jaktområden i samtliga ÄFO som finns i den nationella väljarkatalogen. Den är en teknisk provkörning, inte produktionsinsamling.

**Förkontrollen skriver aldrig till dagliga snapshots, regional pilot-historik eller produktionsdata.** Resultat och råa diagnostikfiler sparas endast som GitHub Actions-artifact i 30 dagar.

## Urval

- Katalogen uppdateras live från den publika portalen innan provhämtningen.
- Endast `boundary_mode=current` används.
- Endast katalograder med slutår minst det begärda jaktåret väljs.
- Standard är ett jaktområde per ÄFO, vilket ger geografisk/organisatorisk täckning över landet snarare än ett stort urval från ett fåtal län.
- Kända pilotidentiteter 724577 (Hörneåns ÄSO) och 718148 (Gräsmyrs VVO) hoppas över för att undvika dubbelinsamling.
- Portal-ID behandlas som en observerad källnyckel, inte som permanent geografisk identitet.
- Katalogens ålder kontrolleras; äldre än 14 dagar stoppar provhämtningen.

## Körning

Workflow: `National Älgdata preflight` (manuell `workflow_dispatch`).

Standardinställningar:
- jaktår: minst 2026/2027;
- ett område per aktuellt ÄFO;
- rapport-ID 4;
- högst 180 minuter.

Varje område hämtas separat genom den befintliga `download_statistics.py`. Ett enskilt områdes timeout eller portalproblem registreras som fel och hindrar inte att senare områden provas. Varje anrop har 180 sekunders timeout.

## Resultat och tolkning

Artifact innehåller:
- `selected_candidates.json`: valda områden och täckning per län/ÄFO;
- `national_preflight_summary.json`: resultat per område och total summering;
- en katalog per område med `download-report.json` och eventuell CSV.

Status skiljer mellan lyckad portalhämtning, tillgängliga datarader, tom rapport och fel. En tom tabell betyder inte noll fällda älgar. Ändringar i kumulativa avskjutningsvärden ska inte tolkas som exakta fälldatum.

## Kriterier före full nationell provtagning

1. Alla aktuella län och ÄFO i katalogen finns med i urvalsrapporten, med undantag som redovisas explicit.
2. Portal-ID, län, ÄFO, jaktår och gränsläge matchar mellan katalog och portalrapport.
3. Tomma tabeller är åtskilda från tekniska fel.
4. Misslyckade hämtningar har diagnostik och påverkar inte identiteten för andra områden.
5. Resultaten granskas innan provet utökas till flera områden per ÄFO eller samtliga cirka 3 200 områden.

Ingen daglig nationell workflow eller produktionsarkivering aktiveras av detta steg.
