# Rekonstruktion av Hörneåns historiska område

## Syfte

Bygga en år-för-år-serie som så långt källorna medger motsvarar det område som i dag redovisas som Hörneåns älgskötselområde. Äldre lokala jaktlag och områdesidentiteter ska kopplas till den moderna identiteten med daterade belägg och, när möjligt, officiella beslut och kartgeometrier.

## Nya historiska ledtrådar

En lokal källa, Hörnsjö VVO:s gästbok, ger två användbara uppgifter:

- **2 december 2012:** ett informationsmöte för det nya Hörneåns älgskötselområde beskrivs, och Hörnsjö, Gräsmyr, Mullsjö, Torrböle, Hummelholm och Tallberg nämns som anslutna jaktlag/grupper.
- **5 juli 2015:** en lokal tilldelningsnotis för Hörneåns ÄSO listar Hummelholm, Mullsjö, Tallberg, Gräsmyr, Hörnsjö, Torrböle, Djupsjö, Högland och Nyåker.

Källa: [Hörnsjö VVO:s historiska gästbok](https://www3.olzzon.com/g/g.php?a=s&i=g32-03680-34&m=alla&p=1), särskilt inläggen daterade 2 december 2012, 2 december 2012 och 5 juli 2015.

Det ger **nio lokala jaktlags-/områdesnamn att följa upp**. Källan belägger inte att alla nio var egna registrerade VVO eller ÄSO. Sex namn förekommer i samband med bildandet/anslutningen 2012/13; tre ytterligare namn förekommer i 2015 års lokala tilldelningslista. Det officiella registreringsförhållandet, exakta startår och historiska geometrier behöver fortfarande verifieras.

## Vad som är verifierat i statistikportalen

- Länsstyrelsens statistikportal listar Hörneåns älgskötselområde, beteckning `24-01-02-342-Ä`, internt ID `724577`.
- Samma portal listar Gräsmyrs viltvårdsområde, beteckning `24-01-02-017-A`, internt ID `718148`.
- För Gräsmyrs VVO finns verifierad avskjutning 2010/2011–2012/2013: 15, 17 och 15 älgar.
- Gräsmyrs ID var inte valbart i de testade senare perioderna. Det visar inte att avskjutningen var noll.
- Älgobs för Hörneåns ID kan hämtas med historiska gränser för 2010/2011–2012/2013. Den serien är märkt som historiska gränser och är inte bevis för att Gräsmyrs VVO var identiskt med Hörneåns ÄSO.

Primärkällor för områdesidentitet och beslut: [Länsstyrelsens Älgdata-statistikportal](https://algdata-apps.lansstyrelsen.se/algdata-apps-stat/) och [Länsstyrelsen Västerbotten – älgförvaltning och jaktområden](https://www.lansstyrelsen.se/vasterbotten/djur/jakt-och-vilt/algjakt/algforvaltning-och-jaktomraden.html). Historiska kartor kan sökas via [Länsstyrelsens kartor och geodata](https://www.lansstyrelsen.se/vasterbotten/om-oss/vara-tjanster/kartor-och-geodata.html).

## Aggregationsregler

1. **Skapa en identitet per historiskt område.** Spara officiellt namn, ID, typ, giltighetsår, areal och källa.
2. **Skilj jaktlag från registrerat jaktområde.** En lokal tilldelningslista kan visa jaktlagens namn men bevisar inte att varje lag var ett eget registrerat VVO/ÄSO.
3. **Koppla områden till målområdet med tidsintervall.** En koppling ska ha startår, slutår, typ av förändring och källa: sammanslagning, utökning, namnbyte, omregistrering eller okänd.
4. **Summera avskjutning bara när täckningen är komplett och områdena inte överlappar.** Om två områden överlappar eller gränserna är okända ska årsresultatet markeras som osäkert, inte summeras.
5. **Behandla mål och utfall separat.** Tilldelning/avskjutningsmål är inte samma sak som faktiskt fällda djur.
6. **Beräkna inte ett enkelt medel av kvoter.** Älgobs per mantimme ska aggregeras från underliggande antal observationer och mantimmar om båda finns; annars redovisas delserier separat.
7. **Bevara rapporterad areal per år.** Ändrad areal är en indikator på möjlig gränsförändring och ska inte tyst normaliseras bort.
8. **Saknad data är null, aldrig noll.** En period utan rapport eller ett område som inte går att välja i portalen ska visas som datalucka.
9. **Märk geografi och metod i varje rad.** Använd till exempel `current_boundaries`, `historical_boundaries` eller `unknown`.

## Nästa datainsamlingssteg

- Hämta historiska beslut och kartgränser från Länsstyrelsens WebbGIS/områdesregister.
- Kontrollera om Hörnsjö, Mullsjö, Torrböle, Hummelholm, Tallberg, Djupsjö, Högland och Nyåker var separata registrerade jaktområden eller interna jaktlag inom Hörneåns ÄSO.
- Fastställ vilket jaktår varje lokal enhet började ingå och om gränserna ändrades.
- För varje identifierad historisk registreringsenhet, hämta avskjutningsutfall och övriga statistiktyper i Älgdata.
- Först därefter skapa en separat `hornean_reconstructed_aggregate`-serie med kvalitetsflagga per jaktår.

## Nuvarande status

Nio lokala namn har nu dokumenterats som historiska ledtrådar. Endast Gräsmyrs VVO har ett separat historiskt registrerings-ID och tre normaliserade avskjutningsår i det nuvarande dataunderlaget. Det finns ännu inte tillräckligt officiellt underlag för att summera alla namn som separata områden eller att slå ihop dem till en obruten totalsiffra.


## Arealjämförelse (2026-10-17)

Arealuppgifterna i de inlästa avskjutningsrapporterna visar en tydlig förändring för Hörneåns ÄSO:

| Jaktår | Rapporterad areal |
|---|---:|
| 2013/2014 | 26 777 ha |
| 2014/2015–2017/2018 | 32 355 ha |
| 2018/2019–2019/2020 | 35 506 ha |
| 2020/2021–2022/2023 | 35 567,05 ha |
| 2023/2024–2025/2026 | 37 132,8 ha |

Det innebär +10 355,8 ha eller cirka +38,7 % mellan första och senaste rapportåret. Gräsmyrs VVO redovisas med 4 795 ha 2010/2011–2012/2013. Den historiska Gräsmyr-arealen motsvarar cirka 12,9 % av den rapporterade Hörneåns-arealen 2025/2026. **Detta visar endast relativ storlek, inte att Gräsmyr är helt inneslutet i Hörneåns nuvarande geometri eller att Gräsmyr ska adderas till den.**

Källfil med årsvärden och förändringar: [data/area_annual.csv](../data/area_annual.csv). Årsarealerna är hämtade ur rapporten *Avskjutning med mål — ÄJO* i Älgdata. Ökningarna 2014/15, 2018/19, 2020/21 och 2023/24 är kandidater för kontroll mot ändringsbeslut och historiska kartor, inte i sig bevis på exakt gränsändring.

### Slutsats om arealmatchning

- Endast Gräsmyrs VVO har en historisk areal i nuvarande underlag (4 795 ha).
- De övriga åtta lokala namnen saknar ännu verifierade registrerade arealer och separata gränspolygoner.
- Det går därför inte att summera de nio namnen eller testa om deras arealer tillsammans motsvarar 37 132,8 ha.
- Nästa steg är att hämta nuvarande och historiska polygoner samt beslut från Länsstyrelsens karttjänst/områdesregister. Beräkna polygonareal i ett lämpligt projicerat koordinatsystem, jämför unionen av historiska polygoner med dagens polygon, och redovisa täckningsgrad, överlapp och yta utanför. Rapportera separat både geometrisk polygonarea och den administrativa areal som Älgdata redovisar; de kan skilja sig.

## Tidsatt rekonstruktion: möjlig etappvis anslutning

Det är möjligt att jaktlag eller marker anslöts vid olika jaktår. Alla namn ska därför ha separat från-/till-jaktår; vi får inte anta att dagens Hörneåns ÄSO hade samma geografiska täckning under hela statistikserien.

En lokal källa, Hörnsjö VVO:s gästbok (https://www3.olzzon.com/g/g.php?a=s&i=g32-03680-34&m=alla&p=1), nämner sex namn i bildande-/anslutningssammanhang den 2 december 2012 och listar nio namn i en lokal tilldelningsnotis den 5 juli 2015. För de sex första är detta belägg för omnämnande i det sammanhanget senast 2012, inte fastställd juridisk anslutningsdag. För Djupsjö, Högland och Nyåker fastställer 2015-listan endast att de redovisades då, inte att de anslöt då.

Hörneåns rapporterade areal ökar från 26 777 ha 2013/14 till 32 355 ha 2014/15 (+5 578 ha), 35 506 ha 2018/19 (+3 151 ha), 35 567,05 ha 2020/21 (+61,05 ha) och 37 132,8 ha 2023/24 (+1 565,75 ha). Dessa steg kan användas för att prioritera sökningen efter beslut men bevisar inte i sig någon viss anslutning. De kan även bero på korrigeringar eller gränsjusteringar.

Fil `data/area_membership_timeline.csv` håller isär första källomnämnande, giltighetsår och bekräftat anslutningsdatum. Okända år lagras som `unknown`; första omnämnande eller arealförändring får aldrig automatiskt omvandlas till ett påstått anslutningsår. Nästa steg är att hitta Länsstyrelsens beslut, äldre älgskötselplaner och historiska polygoner och sedan kontrollera täckning/överlapp innan en avskjutningsserie rekonstrueras.

## Tidigare källa som listar samtliga nio jaktlag (2026-10-17)

Hörnsjö VVO:s gästbok innehåller en post daterad **14 december 2014** med rubriken/innehållet om avskjutning och tilldelning till och med vecka 44. Den listar Hörnsjö, Gräsmyr, Mullsjö, Torrböle, Tallberg, Djupsjö, Hummelholm, Högland och Nyåker. Källa: https://www3.olzzon.com/g/g.php?a=s&i=g32-03680-34&m=alla&p=1 (post nr 234).

Det här flyttar det tidigaste belägget för Djupsjö, Högland och Nyåker från 2015 till senast **14 december 2014**. Det bevisar dock inte att de anslöt just 2014/15: listan visar att lagen redovisades inom sammanhanget för Hörneåns ÄSO då. En faktisk anslutningsdag eller giltighetsperiod måste fortfarande bekräftas från officiella beslut, äldre skötselplaner eller kartunderlag.

Den tidigare källan från **2 december 2012** fortsätter att vara belägg för de sex namn som nämndes i bildande-/anslutningssammanhang. Tidslinjen skiljer nu på första lokala belägg och formellt verifierat anslutningsdatum.


## Källkontroll och datumrättning (2026-10-17)

Vid kontroll av originalposterna i Hörnsjö VVO:s gästbok rättas två datum som tidigare återgetts fel:
- **Post 161 är daterad 2 december 2012** och listar Hörnsjö, Gräsmyr, Mullsjö, Torrböle, Hummelholm och Tallberg som jaktlag anslutna till det nya älgskötselområdet.
- **Post 163 är daterad 13 december 2012** och upprepar listan i samband med informationsmötet.
- **Post 168 är daterad 25 mars 2013** och säger att Hörneåns ÄSO bildats under vintern och att skribentens jaktlag gått med.
- **Post 234 är daterad 14 december 2014**, inte 23 november. Den innehåller avskjutning till och med vecka 44 och tilldelning för samtliga nio namn. Post 233 är den som är daterad 23 november 2014 och innehåller inte denna nio-radiga tabell.

Originalkälla: https://www3.olzzon.com/g/g.php?a=s&i=g32-03680-34&m=alla&p=1. Den här rättningen gäller källornas publiceringsdatum. Den fastställer inte i sig exakta juridiska anslutningsdatum eller historiska gränser.


## Historiska jaktlagsvärden från lokala notiser (2026-10-17)

En separat tabell i `data/historical_team_harvest_allocations.csv` lagrar jaktlagsdata från två lokala notiser:
- **Post 234, daterad 14 december 2014:** avskjutning till och med vecka 44 samt vuxentilldelning per jaktlag för jaktåret 2014/15.
- **Post 242, daterad 5 juli 2015:** vuxentilldelning per jaktlag för jaktåret 2015/16. Texten anger totalt 59 vuxna älgar för hela ÄSO.

2014 års redovisade avskjutning summerar till 30 tjurar, 26 hondjur och 53 kalvar till och med vecka 44. 2015 års tilldelning summerar till 59 vuxna. I 2014 års tabell är Hummelholm förkortat H-holm. Värdena beskriver jaktlagens interna redovisning, inte fristående registrerade områden. De ska inte summeras med Älgdatas områdesstatistik, eftersom det skulle kunna dubbelräkna samma fällda djur.

Dessa två snapshots kan användas för att följa vilka lokala namn som redovisades vid respektive tidpunkt, men de bevisar inte formella anslutningsdatum eller geografisk täckning. Källan är https://www3.olzzon.com/g/g.php?a=s&i=g32-03680-34&m=alla&p=1.

## Historisk arealmatchning mot äldre Nordmalingsområden (2026-10-17)

En publicerad SVT-lista med titeln [Älgtilldelning 2012](https://www.yumpu.com/sv/document/view/27615173/pdf-dokument-algtilldelning-2012-svt) innehåller arealer för äldre VVO och jaktlag. Den jämfördes med Hörneåns rapporterade areal per jaktår i data/area_annual.csv. Resultaten lagras som kandidater i data/historical_area_crosswalk_candidates.csv.

### Exakta aritmetiska träffar

1. **Basår 2013/14:** Gräsmyrs VVO (4 795 ha) + Mullsjö VVO (3 492 ha) + Tallbergslidens VVO (3 172 ha) + Hummelholms VVO (5 508 ha) + Hörnsjö VVO (6 601 ha) + Torrböle VVO (3 209 ha) = **26 777 ha**, exakt samma som Hörneåns ÄSO:s rapporterade areal 2013/14.
2. **Aritmetisk träff för 2014/15:** Djupsjö VVO (2 506 ha) + Nyåkers VVO (2 568 ha) + en post på 504 ha = **5 578 ha**, samma som Hörneåns rapporterade arealökning. Flerårsuttaget från Älgdata visar emellertid att registrering 24-01-02-183-A redan hade 504 ha från 2010/11. Arealsumman är därför en ledtråd, inte belägg för att denna enhet anslöt 2014/15 eller för att den motsvarar Högland.
3. **Ökning 2018/19:** Öre-Brattfors VVO anges till **3 151 ha**, exakt samma som ökningen från 32 355 till 35 506 ha. Kopplingen till Hörneåns ÄSO har inte verifierats.
4. **Ökning 2023/24:** Hallens VVO anges till 1 553 ha, nära men inte exakt ökningen 1 565,75 ha (skillnad 12,75 ha). Detta är en svag hypotes, inte en matchning.

### Tolkning

De tre första träffarna ger en konkret prioriteringsordning för att söka historiska registreringsbeslut och kartor. Den exakta basårssumman är starkt indicium på en möjlig sammansättning av den rapporterade arealen men bevisar inte identiska polygoner. En exakt summa kan bero på avrundning, gemensamma gränser eller sammanträffande; historiska områden kan också ha överlappat, ändrats eller varit delar av en annan registreringsenhet. Arealsteget ska inte automatiskt tolkas som anslutningsår.

Nästa kontroll är att jämföra officiella polygoner eller beslut för 2013/14, 2014/15 och 2018/19 och kontrollera om de föreslagna äldre VVO-områdena faktiskt motsvarar Hörneåns geografi. VK:s artikel [Nordmalings älgtilldelning (2011)](https://www.vk.se/2011-07-08/nordmalings-algtilldelning) är ytterligare en relevant äldre källa att jämföra mot. De arealvärden som använts här är hämtade från den separat publicerade 2012-listan.
## Ytterligare kontroll: oidentifierad post och registerdigitalisering

Den lokala tilldelningslistan från 14 december 2014 innehåller nio namn. Jämfört med de sex namn som nämns i bildande-/anslutningssammanhang 2012/13 är de tre ytterligare namnen Djupsjö, Högland och Nyåker. En tidigare hypotes var att ökningen 2014/15 motsvarade Djupsjö (2 506 ha) + Nyåker (2 568 ha) + posten `01-02-183` (504 ha). Den senare posten hade dock redan 504 ha 2010/11–2012/13 enligt officiell Älgdata. Hypotesen kan därför inte användas som belägg för anslutning just 2014/15, och Högland får inte kopplas till registreringen utan karta eller beslut.

En viktig alternativ förklaring till senare arealsteg är ändrad register- och arealberäkning. Länsstyrelsen Västerbottens årsredovisning för 2020 beskriver att ett nytt administrativt system infördes, att jaktområdenas geometrier behövde kontrolleras och föras över och att nya registreringsbeslut med kartor och fastighetslistor skickades ut. Länsstyrelsens information om kvalitetssäkring förklarar dessutom att arealer i registreringsbeslut beräknas digitalt utifrån Lantmäteriets fastighetsskikt och att endast registrerad landareal ligger till grund för tilldelningen. Se [årsredovisning 2020](https://www.lansstyrelsen.se/download/18.8cd5a1b19362fb4fc2370f/1732539429770/%25C3%2585rsredovisning%2520L%25C3%25A4nsstyrelsen%2520V%C3%A4sterbotten%25202020.pdf) och [information om kvalitetssäkring av älgjaktområden](https://www.lansstyrelsen.se/download/18.4adf753a1791c8ec4551a426/1622009058466/Information-om-kvalitetss%C3%A4kring-av-%C3%A4lgjaktomr%C3%A5den.pdf).

Det betyder att en ändring i rapporterad areal – särskilt kring den period då geometrier digitaliserades och registreringsbeslut uppdaterades – inte automatiskt betyder att ett nytt område anslöts. För att styrka en faktisk anslutning behövs registreringsbeslut, skötselplan eller jämförbara historiska gränser. De exakta aritmetiska träffarna används därför som sökspår, inte som fastställd historik.

## Uppdatering efter fler officiella Älgdata-skärmbilder (2026-10-17)

Ytterligare tre poster från Länsstyrelsens statistikportal har dokumenterats för jaktåret 2009/2010 med urvalet **historiska gränser**:
- Djupsjö VVO, registreringsnummer `24-01-02-093-A`, 2 506 ha.
- Tallbergslidens VVO, `24-01-02-008-A`, 3 172 ha.
- Nyåkers VVO, `24-01-02-052-A`, 2 568 ha.

Värdena har transkriberats från användarens skärmbilder av den officiella portalen och sparats i `data/official_historical_area_stats_2009_2010_additional.csv`. Huvudtabellen för de fem första områdena finns i `data/official_historical_area_stats_2009_2010.csv`. Detta är en dokumenterad transkription från myndighetskällan, inte ett direkt API-uttag.

### Högland och de namnlösa posterna

Den publicerade listan *Älgtilldelning 2012* visar en namnlös post med kod `01-02-183` och 504 ha. Officiell Älgdata visar att modern portalregistrering `24-01-02-183-A` hade 303 ha 2009/10 och 504 ha från 2010/11. Den aritmetiska summan Djupsjö (2 506) + Nyåker (2 568) + 504 = 5 578 ha matchar Hörneåns rapporterade arealsteg 2014/15, men eftersom 504-ha-arealen redan fanns flera år tidigare visar summan inte när eller om denna enhet anslöts till Hörneåns.

Viktigt: samma lista innehåller även andra poster utan namn, exempelvis `01-02-098` med 340 ha. Den koden matchar starkt `24-01-02-098-A — Höglågdal jaktområde` (340 ha i 2009/10–2012/13). Högland förekommer i en lokal tilldelningslista från 2014 men har ännu inte kopplats till `24-01-02-183-A` eller någon annan registrering. Inget av detta bevisar att Högland saknade separat registrering — endast att sambandet inte har verifierats.

Officiell allmän vägledning: Länsstyrelsen beskriver att älgskötsel- och licensområden registreras av myndigheten och att ändringar kräver ansökan/beslut ([Älgförvaltning och jaktområden](https://www.lansstyrelsen.se/vasterbotten/djur/jakt-och-vilt/algjakt/algforvaltning-och-jaktomraden.html)). För att sluta frågan behövs historiskt registerutdrag, registreringsbeslut med karta/fastighetslista eller bekräftelse från Länsstyrelsen Västerbotten.

## Portalens säsongsfiltrerade sökning efter historiska ID:n (2026-10-17)

En ny Playwright-inspektion ställde uttryckligen in rapporttypen `Avskjutning med mål — ÄJO`, Västerbottens län och jaktåret 2009/2010 innan den läste områdesväljaren i alla fem ÄFO och båda gränslägena. Körningen var framgångsrik och artifact finns från GitHub Actions-körningen [39066281476](https://github.com/dahlinrobert-lgtm/alg-grasmyr/actions/runs/39066281476).

I Sydöstra ÄFO visades följande historiska val i portalens områdesväljare:
- `24-01-02-098-A — Höglågdal jaktområde`, internt portal-ID `718169`. Detta är en stark kandidat till den namnlösa posten `01-02-098` (340 ha) i 2012-listan, eftersom kodens sifferdelar överensstämmer och portalen nu ger området ett namn. Den äldre arealen ska kontrolleras i den separat hämtade avskjutningsrapporten innan arealkopplingen behandlas som helt bekräftad.
- `24-01-02-183-A`, internt portal-ID `718179`, visas utan områdesnamn. Den motsvarar den äldre koden `01-02-183` i portalens registreringsnummerstruktur. Det officiella flerårsuttaget visar 303 ha 2009/10 och 504 ha 2010/11–2012/13. Portal-ID och tidsseriens arealsteg är verifierade, men historiskt namn och koppling till det lokala jaktlaget Högland är fortfarande okända.

Sökningen gav även namnet `HÖGLAND-VACKERLIDEN JAKTLAG` under Mellersta ÄFO (`24-21-01-171-A`) och `LÅNGSELE-HÖGLANDS JAKTLAG` under Sydvästra ÄFO (`24-25-91-007-A`). Dessa ligger i andra förvaltningsområden och får **inte** identifieras med det lokala Högland som nämns i den äldre tilldelningslistan för Hörneåns ÄSO. Namnträff i sig bevisar inte geografisk identitet.

De övriga historiska områdena i Sydöstra ÄFO hade följande interna portal-ID:n i samma inspektion: Mullsjö 718143, Tallbergslidens 718145, Gräsmyr 718148, Hörnsjö 718150, Hummelholm 718153, Nyåker 718155, Djupsjö 718168 och Torrböle 718170. Detta gör det möjligt att hämta deras tabellrader reproducerbart med `scripts/download_statistics.py`.

Källfil: `data/portal_area_crosswalk_2009_2010.csv`. Automatiserat uttag: `.github/workflows/download-2009-historical-areas.yml`. Den första oårsspecifika inspektionen ska inte användas för slutsatser om saknade historiska områden; den korrigerade inspektionen med jaktår 2009/2010 är den relevanta.

## Verifierat officiellt tabelluttag för 2009/2010 (2026-10-17)

Ett automatiserat Playwright-uttag från Länsstyrelsens publika Älgdata-portal kördes med rapporttypen `Avskjutning med mål — ÄJO`, Västerbottens län, Sydöstra ÄFO, urvalet **historiska gränser** och jaktåret 2009/2010. Samtliga tio separata områdesuttag i [GitHub Actions-körning 39066438548](https://github.com/dahlinrobert-lgtm/alg-grasmyr/actions/runs/39066438548) avslutades utan rapporterade fel. De visade datauppgifterna finns samlade i `data/official_historical_area_stats_2009_2010_full.csv`, med portal-ID och källa per rad.

| Äldre kod | Portalregistrering / namn | Rapporterad areal 2009/10 | Fällda totalt |
|---|---|---:|---:|
| 01-02-006 | 24-01-02-006-A Mullsjö VVO | 3 492 ha | 9 |
| 01-02-008 | 24-01-02-008-A Tallbergslidens VVO | 3 172 ha | 12 |
| 01-02-017 | 24-01-02-017-A Gräsmyrs VVO | 4 795 ha | 18 |
| 01-02-028 | 24-01-02-028-A Hörnsjö VVO | 6 601 ha | 23 |
| 01-02-045 | 24-01-02-045-A Hummelholms VVO | 5 508 ha | 22 |
| 01-02-052 | 24-01-02-052-A Nyåkers VVO | 2 568 ha | 10 |
| 01-02-093 | 24-01-02-093-A Djupsjö VVO | 2 506 ha | 13 |
| 01-02-098 | 24-01-02-098-A Höglågdal jaktområde | 340 ha | 1 |
| 01-02-100 | 24-01-02-100-A Torrböle VVO | 3 210 ha | 14 |
| 01-02-183 | 24-01-02-183-A (visningsnamn saknas) | 303 ha | 2 |

### Tolkning av de två namnlösa raderna i 2012-listan

- **01-02-098 / Höglågdal:** den säsongsfiltrerade portalrapporten visar exakt 340 ha för `24-01-02-098-A`, och 2012-listan visar en namnlös post `01-02-098` på 340 ha. Kodsekvens, areal och det officiella portalnamnet ger en stark korsreferens. Äldre polygonidentitet bör ändå kontrolleras mot karta eller registreringsbeslut.
- **01-02-183 / okänt namn:** den säsongsfiltrerade portalrapporten visar `24-01-02-183-A` (intern-ID 718179) med **303 ha 2009/10 och 504 ha från 2010/11 till 2012/13**. Den tidigare arealkonflikten mellan 303 och 504 ha är alltså förklarad av årtalet, men orsaken till själva ökningen 2010/11 är ännu inte fastställd. Namn och eventuell koppling till det lokala jaktlaget Högland är fortfarande obekräftade.
- Summeringen Djupsjö (2 506 ha) + Nyåker (2 568 ha) + 504 ha = 5 578 ha matchar aritmetiskt Hörneåns arealsteg 2014/15. Men registrering `24-01-02-183-A` hade 504 ha redan 2010/11–2012/13. Summan bevisar därför varken en anslutning under 2014/15 eller att registreringen är Högland.

### Ytterligare kontroll

Flerårsuttaget för `24-01-02-183-A` och `24-01-02-098-A` är nu klart. Det visar att 183:s arealsteg inträffade 2010/11, och att Höglågdal låg kvar på 340 ha under hela perioden. Nästa fråga är varför 183 ändrades under 2010/11 och vilken geografi/beslutshistorik den omfattar. De lokala delområdenas statistik ska fortfarande hållas åtskild från Hörneåns ÄSO:s egen avskjutning tills geografisk täckning och överlapp har verifierats.

## Verifierad arealserie för registrering 24-01-02-183-A (2026-10-17)

Uttaget av de två kritiska registreringarna för 2009/10–2012/13 slutfördes utan fel i [GitHub Actions-körning 39067137153](https://github.com/dahlinrobert-lgtm/alg-grasmyr/actions/runs/39067137153). Portalens rapport *Avskjutning med mål — ÄJO*, med historiska gränser, visar följande för registrering `24-01-02-183-A` (internt ID 718179; namn saknas):

| Jaktår | Rapporterad areal | Fällda totalt | Avskjutningsmål totalt |
|---|---:|---:|---:|
| 2009/2010 | 303 ha | 2 | 1 |
| 2010/2011 | 504 ha | 1 | 1 |
| 2011/2012 | 504 ha | 1 | 1 |
| 2012/2013 | 504 ha | 3 | 4 |

Det här löser en del av den tidigare arealfrågan: **ökningen med 201 ha inträffar mellan jaktåren 2009/10 och 2010/11 i portalens serie.** Den äldre tilldelningslistan från 2012 anger 504 ha för kod `01-02-183`, vilket stämmer med portalens areal från 2010/11 och framåt. Det verkar alltså inte vara en kvarstående 303/504-konflikt mellan källorna; de beskriver olika jaktår.

Däremot fastställer arealserien inte varför arealen ändrades 2010/11 (t.ex. en faktisk gräns-/anslutningsändring eller uppdatering av register-/arealberäkning) och inte heller vilket lokalt jaktlag den namnlösa registreringen motsvarar. En lokal tilldelningslista från 2014 nämner Högland, men det finns ännu inget beslut eller kartunderlag som knyter namnet till `24-01-02-183-A`. Högland ska därför fortsatt vara oidentifierat i registerkopplingen.

Samma perioduttag för `24-01-02-098-A — Höglågdal jaktområde` visar stabil areal **340 ha** alla fyra säsonger 2009/10–2012/13. Det stärker kopplingen till den namnlösa raden `01-02-098` med 340 ha i 2012-listan.

De årsvisa värdena för `24-01-02-183-A` finns i `data/official_area_history_24-01-02-183-A_2009-2013.csv`. Den fullständiga ettårsbaserade tvärsnittstabellen för tio områden finns i `data/official_historical_area_stats_2009_2010_full.csv`. Fortsatt sammanräkning med Hörneåns ÄSO kräver fortfarande verifierad geografisk täckning och överlapp; rapporterade delområden får inte läggas ovanpå ÄSO-totalen automatiskt.

## Lokalhistorisk geografisk ledtråd för Högland (2026-10-17)

Nordmalings kommuns publicerade inventering *1988 inventering Ledusjö, Norrmark, Baggård, Djupsjö, Högland, Sunnansjö, Stavsjöholm* beskriver Höglands by som belägen på en uppodlad högplatå mellan Djupsjö, Orrböle och Hummelholms skogsskiften och anger att Högland historiskt var ett nybygge på Djupsjö bys skog. Källa: [Nordmalings kommuns inventering, 1988](https://www.nordmaling.se/download/18.38e5fa29193b39ee26d14546/1736343605147/1988%20inventering%20Ledusj%C3%B6%20Norrmark%20Bagg%C3%A5rd%20Djupsj%C3%B6%20H%C3%B6gland%20Sunnansj%C3%B6%20Stavsj%C3%B6holm.pdf).

Detta är relevant lokalhistorisk geografi och stödjer att namnet Högland hör hemma i närområdet kring Djupsjö/Hummelholm. Det **bevisar inte** att jaktlaget Högland i den lokala tilldelningslistan är samma enhet som den namnlösa älgjaktregistreringen `24-01-02-183-A`. En kulturmiljöinventering beskriver byn och historisk markbakgrund, inte registreringsnummer eller älgjaktgränser.

Länsstyrelsens officiella information säger att ändringar av registrerade älgjaktområden, såsom tillägg eller borttagning av fastigheter, sker genom ansökan och beslut. För att koppla det lokala Högland till registrering `24-01-02-183-A` krävs därför fortfarande historiskt beslut, karta/fastighetsbilaga, äldre registerutdrag eller skriftlig bekräftelse från Länsstyrelsen. Se [Älgförvaltning och jaktområden](https://www.lansstyrelsen.se/vasterbotten/djur/jakt-och-vilt/algjakt/algforvaltning-och-jaktomraden.html).



## Officiell registrering 24-01-02-183-A: 303 till 504 ha (2026-10-17)

En säsongsfiltrerad rapport i Länsstyrelsernas Älgdata visar en registrering med beteckningen `24-01-02-183-A`, internt portal-ID `718179`, men utan visat områdesnamn. Rapporterad areal är 303 ha för 2009/2010 och 504 ha för 2010/2011, 2011/2012 och 2012/2013. Det innebär en ändring på +201 ha mellan 2009/2010 och 2010/2011.

Detta förklarar varför den äldre listan från 2012 anger en onamngiven post med koden `01-02-183` och arealen 504 ha. Det är en identifiering av registreringsposten och dess arealserie, **inte** en identifiering av jaktlaget som Högland. Den lokala notisen från 2014 nämner Högland, men inga officiella beslut eller polygoner kopplar ännu Högland till `24-01-02-183-A`.

Den nya uppgiften ändrar hur arealhypoteserna ska tolkas: 504 ha fanns redan i den redovisade arealen 2010/2011–2012/2013. Därför kan just dessa 504 ha inte i sig förklara Hörneåns ÄSO:s senare arealökning med 5 578 ha år 2014/2015. Den senare ökningen kräver en separat förklaring — exempelvis flera registrerings-/gränsändringar, annan geometri eller arealberäkning — som måste kontrolleras mot beslut och kartor.

### Kvarstående verifiering

- Begär registreringsbeslutet för `24-01-02-183-A`, särskilt ändringen från 303 till 504 ha inför 2010/2011.
- Begär karta och fastighetsförteckning som hör till beslutet och eventuella senare ändringsbeslut.
- Kontrollera om handlingen nämner Högland, Djupsjö, Orrböle eller andra lokala namn.
- Jämför den historiska polygonen med Hörneåns gräns för 2013/2014 och senare säsonger innan avskjutning aggregeras.
- Behåll `area_183_historic` som separat identitet med okänt namn och uteslut den från rekonstruerade totalsummor tills identitet och överlapp är verifierade.

Källor: [Länsstyrelsernas Älgdata](https://algdata-apps.lansstyrelsen.se/algdata-apps-stat/) och [Länsstyrelsen Västerbotten – älgförvaltning och jaktområden](https://www.lansstyrelsen.se/vasterbotten/djur/jakt-och-vilt/algjakt/algforvaltning-och-jaktomraden.html). Portaluppgiften är dokumenterad från säsongsfiltrerad rapport och skärmbaserat uttag; den tomma namnkolumnen ska bevaras som sådan.
