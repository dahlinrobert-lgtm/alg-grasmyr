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
2. **Ökning 2014/15:** Djupsjö VVO (2 506 ha) + Nyåkers VVO (2 568 ha) + en oidentifierad post på 504 ha = **5 578 ha**, exakt samma som ökningen från 26 777 till 32 355 ha. Den oidentifierade 504-ha-posten ska inte automatiskt kopplas till Högland eller något annat lokalt namn.
3. **Ökning 2018/19:** Öre-Brattfors VVO anges till **3 151 ha**, exakt samma som ökningen från 32 355 till 35 506 ha. Kopplingen till Hörneåns ÄSO har inte verifierats.
4. **Ökning 2023/24:** Hallens VVO anges till 1 553 ha, nära men inte exakt ökningen 1 565,75 ha (skillnad 12,75 ha). Detta är en svag hypotes, inte en matchning.

### Tolkning

De tre första träffarna ger en konkret prioriteringsordning för att söka historiska registreringsbeslut och kartor. Den exakta basårssumman är starkt indicium på en möjlig sammansättning av den rapporterade arealen men bevisar inte identiska polygoner. En exakt summa kan bero på avrundning, gemensamma gränser eller sammanträffande; historiska områden kan också ha överlappat, ändrats eller varit delar av en annan registreringsenhet. Arealsteget ska inte automatiskt tolkas som anslutningsår.

Nästa kontroll är att jämföra officiella polygoner eller beslut för 2013/14, 2014/15 och 2018/19 och kontrollera om de föreslagna äldre VVO-områdena faktiskt motsvarar Hörneåns geografi. VK:s artikel [Nordmalings älgtilldelning (2011)](https://www.vk.se/2011-07-08/nordmalings-algtilldelning) är ytterligare en relevant äldre källa att jämföra mot. De arealvärden som använts här är hämtade från den separat publicerade 2012-listan.
## Ytterligare kontroll: oidentifierad post och registerdigitalisering

Den lokala tilldelningslistan från 14 december 2014 innehåller nio namn. Jämfört med de sex namn som nämns i bildande-/anslutningssammanhang 2012/13 är de tre ytterligare namnen Djupsjö, Högland och Nyåker. Arealhypotesen för 2014/15 består av Djupsjö (2 506 ha) + Nyåker (2 568 ha) + den oidentifierade posten `01-02-183` (504 ha). Därför är Högland en möjlig identitet för posten på 504 ha, men 2012-listan saknar namn och det finns ännu ingen källa som knyter ihop Högland med koden. Behandla det som en kandidat, inte som en identifiering.

En viktig alternativ förklaring till senare arealsteg är ändrad register- och arealberäkning. Länsstyrelsen Västerbottens årsredovisning för 2020 beskriver att ett nytt administrativt system infördes, att jaktområdenas geometrier behövde kontrolleras och föras över och att nya registreringsbeslut med kartor och fastighetslistor skickades ut. Länsstyrelsens information om kvalitetssäkring förklarar dessutom att arealer i registreringsbeslut beräknas digitalt utifrån Lantmäteriets fastighetsskikt och att endast registrerad landareal ligger till grund för tilldelningen. Se [årsredovisning 2020](https://www.lansstyrelsen.se/download/18.8cd5a1b19362fb4fc2370f/1732539429770/%25C3%2585rsredovisning%2520L%25C3%25A4nsstyrelsen%2520V%C3%A4sterbotten%25202020.pdf) och [information om kvalitetssäkring av älgjaktområden](https://www.lansstyrelsen.se/download/18.4adf753a1791c8ec4551a426/1622009058466/Information-om-kvalitetss%C3%A4kring-av-%C3%A4lgjaktomr%C3%A5den.pdf).

Det betyder att en ändring i rapporterad areal – särskilt kring den period då geometrier digitaliserades och registreringsbeslut uppdaterades – inte automatiskt betyder att ett nytt område anslöts. För att styrka en faktisk anslutning behövs registreringsbeslut, skötselplan eller jämförbara historiska gränser. De exakta aritmetiska träffarna används därför som sökspår, inte som fastställd historik.