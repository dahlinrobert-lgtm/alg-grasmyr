# Bearbetade kopior

Här sparas automatiskt skapade CSV-kopior och manifest från `scripts/prepare_export.py`. Kopiorna behåller kalkylbladens rader och är inte en normaliserad analysdatabas. Behåll originalfiler i `data/raw/`.

När en första verklig export har inspekterats skapas en källspecifik normalisering med dokumenterade fältmappningar.


## Första faktiska datauttaget

`avskjutning_mal_ajo_hornean_2013-2020.csv` innehåller 7 rader från Länsstyrelsernas Älgdata, rapporten **Avskjutning med mål – ÄJO**, för `24-01-02-342-Ä - Hörneåns älgskötselområde`, portal-ID `724577`, Västerbottens län/Sydöstra ÄFO. Urvalet använde nuvarande gränser; tabellen innehåller jaktåren 2013/2014–2019/2020. Uppgifterna 2010/2011–2012/2013 saknas i just den här tabellen och har inte satts till noll.

Fälten är översatta från statistikportalens grupperade tabellrubriker. Originalets visningsvärden bevaras, inklusive decimalcomma och procenttecken. Värdena i `fallda_*` beskriver faktiskt fällda älgar. Värdena i `avskjutningsmal_*` beskriver avskjutningsmålet och ska inte tolkas som faktisk avskjutning. Nyttjandegrad är rapportens nyttjandegrad av avskjutningsmålet.

Se motsvarande `.metadata.json` för källa, filter och begränsningar. Nya uttag sparas med egna urvalsmetadata i stället för att skriva över äldre data.


## Sammanställda uttag (2026-10-17)

- `avskjutning_mal_ajo_hornean_2013-2026.csv`: 13 säsonger, 2013/2014–2025/2026, Hörneåns ÄSO. Sammanställd från två rapportuttag med nuvarande gränser.
- `avskjutning_mal_ajo_hornean_2013-2026.metadata.json`: källa, filter, period och total avskjutning per säsong.
- `avskjutning_mal_ajo_grasmyr_2010-2013.csv`: 3 säsonger, 2010/2011–2012/2013, Gräsmyrs VVO.
- `avskjutning_mal_ajo_grasmyr_2010-2013.metadata.json`: källa, filter, period och notering om att området inte fanns i listan för aktuella gränser i senare period.

Den senaste portalen gav ingen rad för Gräsmyrs VVO efter 2012/2013 och gick inte att välja för perioden 2020/2021–2025/2026 med nuvarande gränser. Detta ska tolkas som att den valda områdesidentiteten/rapporten inte ger senare rader, inte som att avskjutningen var noll. Undersök historiska gränser och eventuell övergång till annat område innan du drar slutsatser.


## Övriga statistiktyper (2026-10-17)

För Hörneåns ÄSO har tre rapporttyper fångats för 2020/2021–2025/2026:
- `medelalder_vuxna_hornean_2020-2026.csv`: medelålder och provantal för vuxna handjur/hondjur.
- `slaktvikt_hornean_2020-2026.csv`: slaktvikt (kg) och provantal per kategori, med månadsuppdelningar för kalvar som i källan.
- `algobs_hornean_2020-2026.csv`: älgobs per mantimme, kalv/hondjur- och könsandelar, antal efter observationskategori samt statistisk säkerställning.

Råa tabellfångster ligger i `data/raw/portal_tables/`. Se `other-statistics-hornean-2020-2026.metadata.json` för fältförklaringar och `other-statistics-coverage.json` för utfall per område/rapport. Gräsmyrs rapporter för medelålder, slaktvikt och älgobs returnerade noll provantal eller ingen data i de kontrollerade urvalen; detta får inte tolkas som noll fällda eller observerade älgar.
