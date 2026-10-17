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
- [Historisk arealmatchning – äldre VVO-arealer och kandidater för arealsteg](data/historical_area_crosswalk_candidates.csv).
- [Portalens historiska områdeskoder för jaktåret 2009/2010](data/portal_area_crosswalk_2009_2010.csv): säsongsfiltrerade ID:n och försiktigt bedömda kopplingar för de äldre Nordmalingsområdena.
- [Fullständigt officiellt avskjutningsuttag för tio områden 2009/2010](data/official_historical_area_stats_2009_2010_full.csv): rapporterad areal, fällda älgar, avskjutningsmål, nyttjandegrad och portal-ID.
- [Historik för namnlös registrering 24-01-02-183-A, 2009/10–2012/13](data/official_area_history_24-01-02-183-A_2009-2013.csv): bekräftar arealsteget 303 → 504 ha från 2010/11.
- [Officiell flerårstabell för tio historiska områden 2009/10–2012/13](data/official_historical_area_summary_2009_2013.csv): 40 rader med areal, fällda älgar och avskjutningsmål.
- [Workflow: full historisk registergranskning](.github/workflows/audit-historical-area-registers.yml), körning [39067657897](https://github.com/dahlinrobert-lgtm/alg-grasmyr/actions/runs/39067657897) med fullständiga tabeller och diagnostik.
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
