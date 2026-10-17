# Rekonstruktion av Hörneåns historiska område

## Syfte

Bygga en år-för-år-serie som så långt källorna medger motsvarar det område som i dag redovisas som Hörneåns älgskötselområde. Äldre lokala jaktlag och områdesidentiteter ska kopplas till den moderna identiteten med daterade belägg och, när möjligt, officiella beslut och kartgeometrier.

## Nya historiska ledtrådar

En lokal källa, Hörnsjö VVO:s gästbok, ger två användbara uppgifter:

- **5 december 2012:** ett informationsmöte för det nya Hörneåns älgskötselområde beskrivs, och Hörnsjö, Gräsmyr, Mullsjö, Torrböle, Hummelholm och Tallberg nämns som anslutna jaktlag/grupper.
- **5 juli 2015:** en lokal tilldelningsnotis för Hörneåns ÄSO listar Hummelholm, Mullsjö, Tallberg, Gräsmyr, Hörnsjö, Torrböle, Djupsjö, Högland och Nyåker.

Källa: [Hörnsjö VVO:s historiska gästbok](https://www3.olzzon.com/g/g.php?a=s&i=g32-03680-34&m=alla&p=1), särskilt inläggen daterade 5 december 2012, 2 december 2012 och 5 juli 2015.

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
