# Bearbetade kopior

Här sparas automatiskt skapade CSV-kopior och manifest från `scripts/prepare_export.py`. Kopiorna behåller kalkylbladens rader och är inte en normaliserad analysdatabas. Behåll originalfiler i `data/raw/`.

När en första verklig export har inspekterats skapas en källspecifik normalisering med dokumenterade fältmappningar.


## Första faktiska datauttaget

`avskjutning_mal_ajo_hornean_2013-2020.csv` innehåller 7 rader från Länsstyrelsernas Älgdata, rapporten **Avskjutning med mål – ÄJO**, för `24-01-02-342-Ä - Hörneåns älgskötselområde`, portal-ID `724577`, Västerbottens län/Sydöstra ÄFO. Urvalet använde nuvarande gränser; tabellen innehåller jaktåren 2013/2014–2019/2020. Uppgifterna 2010/2011–2012/2013 saknas i just den här tabellen och har inte satts till noll.

Fälten är översatta från statistikportalens grupperade tabellrubriker. Originalets visningsvärden bevaras, inklusive decimalcomma och procenttecken. Värdena i `fallda_*` beskriver faktiskt fällda älgar. Värdena i `avskjutningsmal_*` beskriver avskjutningsmålet och ska inte tolkas som faktisk avskjutning. Nyttjandegrad är rapportens nyttjandegrad av avskjutningsmålet.

Se motsvarande `.metadata.json` för källa, filter och begränsningar. Nya uttag sparas med egna urvalsmetadata i stället för att skriva över äldre data.
