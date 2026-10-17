# Rekonstruktion av Hörneåns historiska område

## Syfte

Bygga en år-för-år-serie som så långt källorna medger motsvarar det område som i dag redovisas som Hörneåns älgskötselområde. Äldre lokala jaktområden, däribland Gräsmyrs VVO, ska kunna kopplas till den moderna identiteten genom en daterad områdeshistorik.

## Vad är verifierat nu?

- Länsstyrelsens statistikportal listar Hörneåns älgskötselområde, beteckning `24-01-02-342-Ä`, internt ID `724577`.
- Samma portal listar Gräsmyrs viltvårdsområde, beteckning `24-01-02-017-A`, internt ID `718148`.
- För Gräsmyrs VVO finns verifierad avskjutning 2010/2011–2012/2013: 15, 17 och 15 älgar.
- Gräsmyrs ID var inte valbart i de testade senare perioderna. Det visar inte att avskjutningen var noll.
- Älgobs för Hörneåns ID kan hämtas med historiska gränser för 2010/2011–2012/2013. Den serien är märkt som historiska gränser och är inte bevis för att Gräsmyrs VVO var identiskt med Hörneåns ÄSO.

Källor: [Länsstyrelsens Älgdata-statistikportal](https://algdata-apps.lansstyrelsen.se/algdata-apps-stat/) och [Länsstyrelsen Västerbotten – älgförvaltning och jaktområden](https://www.lansstyrelsen.se/vasterbotten/djur/jakt-och-vilt/algjakt/algforvaltning-och-jaktomraden.html).

## Aggregationsregler

1. **Skapa en identitet per historiskt område.** Spara officiellt namn, ID, typ, giltighetsår, areal och källa.
2. **Koppla områden till målområdet med tidsintervall.** En koppling ska ha startår, slutår, typ av förändring och källa: sammanslagning, utökning, namnbyte, omregistrering eller okänd.
3. **Summera avskjutning bara när täckningen är komplett och områdena inte överlappar.** Om två områden överlappar eller gränserna är okända ska årsresultatet markeras som osäkert, inte summeras.
4. **Behandla mål och utfall separat.** Tilldelning/avskjutningsmål är inte samma sak som faktiskt fällda djur.
5. **Beräkna inte ett enkelt medel av kvoter.** Älgobs per mantimme ska aggregeras från underliggande antal observationer och mantimmar om båda finns; annars redovisas delserier separat.
6. **Bevara rapporterad areal per år.** Ändrad areal är en indikator på möjlig gränsförändring och ska inte tyst normaliseras bort.
7. **Saknad data är null, aldrig noll.** En period utan rapport eller ett område som inte går att välja i portalen ska visas som datalucka.
8. **Märk geografi och metod i varje rad.** Använd till exempel `current_boundaries`, `historical_boundaries` eller `unknown`.

## Nästa datainsamlingssteg

- Hämta historiska beslut och kartgränser från Länsstyrelsens WebbGIS/områdesregister.
- Identifiera samtliga äldre områden som uppgick i eller lämnade Hörneåns ÄSO och fastställ vilket jaktår varje förändring började gälla.
- Jämför registreringsnummer, areal och gränser mellan år.
- För varje föregångare, hämta avskjutningsutfall och övriga statistiktyper i Älgdata.
- Först därefter skapa en separat `hornean_reconstructed_aggregate`-serie med kvalitetsflagga per jaktår.

## Nuvarande status

Det finns ännu inte tillräckligt officiellt underlag för att på ett säkert sätt summera Gräsmyrs VVO:s historiska utfall med Hörneåns ÄSO:s senare utfall eller att namnge andra föregångare. Projektet har därför en explicit lineage-registerfil i `data/area_lineage.csv` och ska inte presentera en skenbart obruten aggregatserie innan dessa kontroller är klara.
