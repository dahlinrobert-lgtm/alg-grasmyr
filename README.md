# Älgdata – Gräsmyr och Hörneåns älgskötselområde

Projekt för att hämta, versionshantera och analysera älgstatistik från Länsstyrelsernas Älgdata, med särskilt fokus på Gräsmyrs viltvårdsområde och Hörneåns älgskötselområde.

## Datakällor

- [Länsstyrelsernas statistikportal Älgdata](https://algdata-apps.lansstyrelsen.se/algdata-apps-stat/)
- [Länsstyrelsens Älgdata WebbGIS](https://ext-webbgis.lansstyrelsen.se/lst_algdata/)
- [Älgdata – översikt och statistik](https://www.algdata.se/)

Statistikportalen har flera rapporttyper, bland annat avskjutning med mål, medelålder, åldersstruktur, slaktvikt, älgobservationer, biologiska data och viltolyckor. Se [statistikportalen](https://algdata-apps.lansstyrelsen.se/algdata-apps-stat/) och [Älgdatas statistiksida](https://www.algdata.se/statistik/). Vilka rapporter som går att få på ÄJO-nivå varierar.

## Områdesidentiteter

Portalen visar följande områden under **Sydöstra älgförvaltningsområdet**:

| Område | Officiell beteckning i statistikportalen | Internt portal-ID |
|---|---|---:|
| Gräsmyrs viltvårdsområde | `24-01-02-017-A` | `718148` |
| Hörneåns älgskötselområde | `24-01-02-342-Ä` | `724577` |

Detta är två separata val i portalen. De ska inte automatiskt behandlas som samma geografiska enhet. För att länka tidsserierna behövs historik över beslut, områdesgränser och eventuell ändrad rapportering.

## Webbplats

En responsiv statistikwebb publiceras via GitHub Pages från [index.html](index.html) i repositoryts rot. Den visar separat älgstatistik för Hörneåns ÄSO och historiska Gräsmyrs VVO, samt en egen kronhjortsdel där värden inte visas förrän årsdata har verifierats. Webbplatsen markerar områdeshistorik och saknade värden.

## Data som redan finns i repot

- [Hörneåns ÄSO – avskjutning 2013/2014–2025/2026](data/processed/avskjutning_mal_ajo_hornean_2013-2026.csv): 13 säsonger, med både faktiskt fällda älgar, avskjutningsmål och rapporterad nyttjandegrad.
- [Metadata för Hörneåns ÄSO](data/processed/avskjutning_mal_ajo_hornean_2013-2026.metadata.json): källa, områdes-ID, urval och täckningsnoteringar.
- [Gräsmyrs VVO – avskjutning 2010/2011–2012/2013](data/processed/avskjutning_mal_ajo_grasmyr_2010-2013.csv): 3 säsonger i det historiska områdets egen portalserie.
- [Metadata för Gräsmyrs VVO](data/processed/avskjutning_mal_ajo_grasmyr_2010-2013.metadata.json): källa, urval och begränsningar.
- [Hörneåns ÄSO – medelålder 2013/2014–2025/2026](data/processed/medelalder_vuxna_hornean_2013-2026.csv): 13 säsonger.
- [Hörneåns ÄSO – slaktvikter 2013/2014–2025/2026](data/processed/slaktvikt_hornean_2013-2026.csv): 13 säsonger.
- [Hörneåns ÄSO – älgobservationer 2013/2014–2025/2026](data/processed/algobs_hornean_2013-2026.csv): 13 säsonger med nuvarande gränser.
- [Tillägg – älgobs 2010/2011–2012/2013 med historiska gränser](data/processed/algobs_hornean_historical_boundaries_2010-2013.csv): tre äldre säsonger som kompletterar tidslinjen, men ska hållas åtskilda från serien med nuvarande gränser. Källtabellen för hela uttaget finns under [rådata](data/raw/portal_tables/hornean_algobs_ajo_historical_boundaries_2010-2020.csv); [metadata](data/processed/algobs_hornean_historical_boundaries_2010-2013.metadata.json) beskriver urvalet.
- [Metadata för de tre statistikserierna](data/processed/other-statistics-hornean-2013-2026.metadata.json).
- [Äldre deluttag 2020/2021–2025/2026](data/processed/other-statistics-hornean-2020-2026.metadata.json) finns kvar som dokumentation för det första uttaget.
- [Täckning för övriga rapporter](data/processed/other-statistics-coverage.json): rapporttyper med data och rapporter där portalen saknade prov/data.
- [Råa tabellfångster](data/raw/portal_tables/README.md): de ursprungliga rubrikerna och portalens explicita tomdata-meddelanden.

Rapporttypen är **Avskjutning med mål — ÄJO**. I CSV-filerna är `fallda_totalt` faktiskt rapporterat antal fällda älgar. `avskjutningsmal_totalt` är måltalet, inte utfallet. Källans visningsformat har bevarats, exempelvis decimalcomma och procenttecken.

### Viktig täckningslucka för Gräsmyr

Frågan för Gräsmyrs VVO gav data för 2010/2011, 2011/2012 och 2012/2013. För 2020/2021–2025/2026 gick områdes-ID `718148` inte att välja varken med nuvarande eller historiska gränser. Detta betyder **att området inte finns tillgängligt i den valda rapportens/urvalets senare serie**, inte att avskjutningen var noll. Ta reda på om rapporteringen flyttades till en annan områdesidentitet innan serierna knyts ihop.

## Hämta uppgifter på nytt

- [Actions: avskjutning för båda områdena](https://github.com/dahlinrobert-lgtm/alg-grasmyr/actions/workflows/download-statistics.yml) hämtar två jaktårsintervall för varje område och sparar CSV samt diagnostik som ett GitHub Actions-artifact.
- [Actions: fler statistiktyper](https://github.com/dahlinrobert-lgtm/alg-grasmyr/actions/workflows/download-other-statistics.yml) testar medelålder, slaktvikt och älgobservationer för de områdes-/periodkombinationer som går att välja.
- [Guide för datahämtning](docs/acquisition.md)
- [Excel-baserad arealavstämning – registrerade arealer och differenser](data/historical_area_crosswalk_candidates.csv).
- [Officiell flerårstabell för tio historiska områden 2009/10–2012/13](data/official_historical_area_summary_2009_2013.csv): 40 rapporterade rader med areal, fällda älgar och avskjutningsmål.
- [Workflow: full historisk registergranskning](.github/workflows/audit-historical-area-registers.yml), körning [39067657897](https://github.com/dahlinrobert-lgtm/alg-grasmyr/actions/runs/39067657897), med fullständiga tabeller och diagnostik.
- [Portalens historiska områdeskoder för jaktåret 2009/2010](data/portal_area_crosswalk_2009_2010.csv): säsongsfiltrerade ID:n och försiktigt bedömda kopplingar för de äldre Nordmalingsområdena.
- [Fullständigt officiellt avskjutningsuttag för tio områden 2009/2010](data/official_historical_area_stats_2009_2010_full.csv): rapporterad areal, fällda älgar, avskjutningsmål, nyttjandegrad och portal-ID.
- [Historik för namnlös registrering 24-01-02-183-A, 2009/10–2012/13](data/official_area_history_24-01-02-183-A_2009-2013.csv): bekräftar arealsteget 303 → 504 ha från 2010/11.
- [Workflow: hämta historisk statistik för de identifierade områdena](.github/workflows/download-2009-historical-areas.yml): testar avskjutningsrapporten för nio namngivna områden och den namnlösa posten 24-01-02-183-A.
- [Områdesregister](data/area_registry.csv)
- [Datadictionary och kvalitetsregler](docs/data-dictionary.md)

Skripten använder statistikportalens publika webbgränssnitt med Playwright. Avskjutning, medelålder, slaktvikt och älgobs finns nu i separata bearbetade CSV-filer för Hörneåns ÄSO 2013/2014–2025/2026; andra rapporttyper kan fortfarande behöva källspecifik normalisering. Hämtningarna lämnar inga syntetiska nollor för saknade år.

## Lokal körning

Installera beroenden:

```bash
python -m pip install -r requirements.txt
python -m pip install -r requirements-portal.txt
python -m playwright install chromium
```

Inspektera en Excel-fil:

```bash
python scripts/inspect_export.py path/to/export.xlsx
python scripts/prepare_export.py path/to/export.xlsx --out data/processed
```

Hämta en rapport manuellt via portalen:

```bash
python scripts/download_statistics.py \
  --out out/hornean_2020-2025 \
  --area-id 724577 \
  --from-year "2020/2021" \
  --to-year "2025/2026" \
  --boundary-mode current \
  --report-id 4
```

## Kvalitetsregler

1. Behåll original-/råexporter och spara källa, urval, områdes-ID, gränsläge och hämtningstidpunkt.
2. Saknade år är saknade värden, inte nollor.
3. Skilj alltid faktiskt fällda älgar från avskjutningsmål.
4. Jaktår ska behållas som text tills formatet är verifierat.
5. Ändrade områdesgränser och områdes-ID ska dokumenteras; blanda inte statistik från olika geografiska enheter utan belägg.

- [Säsongsvis arealavstämning mot Hörneåns ÄSO](data/area_reconciliation_by_season.csv): visar aritmetiska kandidatmatchningar och kvarstående differenser. Hallens separata registrering i Excel anger 1 567,62 ha 2021/22–2022/23.
- [Jämförelse av original-Excel med historiska respektive nuvarande gränser](data/processed/boundary-comparison-summary.md): jämför registreringsnummer, registrerade arealer och övriga fält för alla säsonger där båda exportvarianterna finns.
- [Registreringshistorik för äldre delområden](data/processed/area-registration-boundary-audit.csv) och [direkt Excel-kontroll av Hörneåns rapporterade areal](data/processed/hornean-area-source-check.csv): källvärden för identifierade registreringsnummer i båda gränsvarianterna.


## Inventering av publicerade Excel-exporter

Den befintliga Excel-granskningen visar följande säsongstäckning i repot:

- **Nuvarande gränser:** 2000/2001–2016/2017 samt 2019/2020–2026/2027.
- **Historiska gränser:** 2012/2013–2016/2017 samt 2019/2020–2026/2027.
- **Lucka i båda exportserierna:** 2017/2018 och 2018/2019.

Det innebär att de tillgängliga nuvarande-gränser-filerna från 2000/2001 och framåt redan är representerade i den granskade säsongsserien; vi ska inte be om att de laddas upp igen. För 2000/2001–2011/2012 finns bara nuvarande-gränser-exporter i den inventerade serien. Åren 2017/2018 och 2018/2019 ska markeras som saknade källfiler, inte fyllas med antaganden. Se [registreringshistoriken från Excel-granskningen](data/processed/area-registration-boundary-audit.csv) och [jämförelsesammanfattningen](data/processed/boundary-comparison-summary.md).

## Källhierarki och granskningsprincip

**Endast myndighetens publicerade Excel-exporter är primärkälla för statistiken i projektet.** Bearbetade CSV-filer, metadata, manuellt sammanställda tabeller och webbplatsens JavaScript är sekundära representationer. Varje redovisat värde ska kunna spåras till en relevant Excel-fil, ett jaktår och en registrering. Vid avvikelse ska Excel-filen styra. En CSV-kopia eller en uppgift från en annan webbplats får inte ersätta originalexporten som facit.

Vid avstämning ska vi skilja mellan:
- **Direkt källvärde:** värde som går att återfinna i Excel-exporten.
- **Beräknat värde:** exempelvis differens mellan två rapporterade arealer; beräkningen ska redovisas.
- **Obekräftad tolkning:** slutsats som inte direkt framgår av Excel-filerna; den ska inte presenteras som statistik eller fastställd områdestillhörighet.

### Excel-baserad tolkning av arealhistoriken

För offentlig statistik i detta projekt används endast myndighetens publicerade Excel-exporter som belägg för registrerade arealer, områdesnamn, registreringsnummer och jaktår. Externa listor, lokala källor och andra webbplatser används inte för att fylla luckor eller fastställa historiska medlemskap.

- **2019/2020:** Den första tillgängliga Excel-exporten efter luckan visar 35 506 ha, 3 151 ha mer än 2016/2017. Öre-Brattfors finns separat med 3 151 ha i Excel 2016/2017. Det är en aritmetisk matchning över en källucka, inte bevis för överföring eller för att förändringen skedde 2018/2019.
- **2020/2021:** rapporterad ökning är 61,05 ha. Ingen motsvarande separat registrering har identifierats i den granskade Excel-serien. Orsaken är okänd; vi antar varken felinmatning eller anslutning.
- **2023/2024:** Hörneåns rapporterade areal ökar med 1 565,75 ha. Hallens finns separat med 1 567,62 ha i Excel 2021/2022 och 2022/2023, en differens på 1,87 ha. Det bevisar inte överföring eller identiska gränser.
- Öre-Brattfors finns separat i tillgängliga filer till och med 2016/2017 men inte i tillgängliga filer från 2019/2020. Hallens finns separat till och med 2022/2023 men saknas separat från 2023/2024.
- Excel-filer för 2017/2018 och 2018/2019 saknas i båda gränsserierna. Övergångar kan därför inte fastställas exakt från det tillgängliga Excel-materialet.

Alla areal- och avskjutningsvärden på webbplatsen ska kontrolleras mot primära Excel-exporter innan de markeras som avstämda. Där en relevant Excel-export eller säsong saknas ska luckan anges öppet.
