# Geografisk kontext och bevisnivå

## Projektkontext från områdeskunnig användare

Projektägaren uppger att de berörda byarna/områdena är geografiskt sammanhängande grannbyar och att Gräsmyrs VVO historiskt utgick från trakt-/fastighetsidentitet: fastigheter i byn kan exempelvis ha beteckningar som **Gräsmyr 1:1** och **Gräsmyr 2:1**, dvs. fastighetsnamn som börjar med GRÄSMYR.

Denna uppgift är viktig kontext för hur den historiska områdesutvecklingen ska undersökas. Den gör det rimligt att pröva en historik där närliggande delområden kan ha införlivats vid olika tidpunkter, i stället för att anta att samtliga byar anslöts samtidigt.

## Nuvarande geometri för Hörneåns ÄSO

Den shapefil som projektägaren lämnade den 18 oktober 2026 har granskats och ska behandlas som projektets nuvarande geografiska referens för Hörneåns älgskötselområde.

| Egenskap | Värde |
|---|---|
| Områdesnamn (`namn_ajo`) | Hörneåns älgskötselområde |
| Områdesnummer (`omrnum`) | 24-01-02-342-Ä |
| Typ (`objtyp`) | Älgskötselomr |
| Älgförvaltningsområde (`namn_afo`) | Sydöstra älgförvaltningsområdet |
| Beslutsdatum (`beslutdat`) | 2023-12-05 |
| Angiven beslutsarea (`bslarea_ha`) | 37 134 ha |
| Koordinatsystem | SWEREF 99 TM, EPSG:3006 |
| Geometri | MultiPolygon, 8 delar |
| Beräknad plan area från koordinaterna | 37 987,07 ha |
| Giltighetstest | Ogiltig geometri; självkorsning rapporterad vid cirka E 729802,259 / N 7069521,380 |

Den beräknade planarean är **853,07 ha större** än attributet `bslarea_ha`. En union av de åtta polygonkomponenterna ger i praktiken samma area som komponenternas summa, så skillnaden förklaras inte av överlapp mellan komponenterna. En geometrireparation med `make_valid` gör geometrin giltig men ändrar inte den beräknade arean på ett meningsfullt sätt.

**Tolkning:** attributet 37 134 ha och geometriarealen 37 987,07 ha ska redovisas separat. Det är ännu inte klarlagt om skillnaden beror på hur beslutsarean definierats, en avvikelse i själva geometriunderlaget eller någon annan dataprocess. Den beräknade arean ska inte ersätta den angivna beslutsarean som officiellt värde.

### Konsekvens för analysen

- Använd geometrin som **referens för rumslig orientering**, men markera den som kvalitetskontrollerad med anmärkning.
- Reparera en arbetskopia före overlay-/skärningsanalyser. Behåll originalfilen oförändrad.
- Kontrollera areaberäkning och gränsunderlag innan resultaten används som exakta hektarvärden.
- Dagens geometri kan hjälpa till att pröva rumsliga samband, men bevisar inte äldre gränser eller formella medlemskapsår.

## Hur kontexten används

Uppgiften ovan är projektägarens geografiska/historiska kontext. Den är **inte ett värde eller en medlemsuppgift som har verifierats i myndighetens publicerade Älgdata-Excel**. Därför används den för att styra vilka samband vi undersöker, men inte ensam för att märka en viss registrering som formellt införlivad eller för att fastställa ett exakt anslutningsår.

För statistik och registrerade uppgifter gäller fortsatt följande källhierarki:

1. **Direkt Excel-belägg:** registreringsnummer, områdesnamn, areal och jaktår som syns i myndighetens publicerade Excel-export.
2. **Aritmetisk observation:** en beräknad differens eller summa av Excel-värden, tydligt redovisad som beräkning.
3. **Geografisk/historisk tolkning:** samband som är rimliga utifrån projektägarens lokalkunskap och mönster i Excel, men som inte är direkt dokumenterade i Excel. Dessa märks som hypotes eller arbetstolkning, inte som fastställd statistik.

## Aktuella spår att pröva

- **Gräsmyr:** Excel visar Gräsmyrs VVO som en separat historisk registrering 2010/2011–2012/2013, med rapporterad areal 4 795 ha. Den senare geografiska relationen till Hörneåns är inte direkt fastställd i de granskade exporterna.
- **Öre-Brattfors:** 3 151 ha som separat registrering i 2017/2018; separat rad saknas i 2018/2019 samtidigt som Hörneåns rapporterade areal ökar med 3 151 ha. Det är en exakt aritmetisk matchning och ett tydligt spår, men inte ensamt bevis för formellt införlivande eller identiska polygoner.
- **Hallen:** 1 567,62 ha som separat registrering 2021/2022 och 2022/2023; separat rad saknas i 2023/2024, då Hörneåns areal ökar med 1 565,75 ha. Differensen är −1,87 ha och måste behållas synlig.
- **2020/2021:** ökningen på 61,05 ha saknar ännu en identifierad separat arealpost som förklarar den. Den ska stå som olöst tills Excel-underlaget ger bättre stöd.

## Nästa analysprincip

Fortsätt säsong för säsong med registreringsnummer som nyckel, inte bara namn eller radposition. Sök efter första/sista förekomst, areal, namnändring och när en separat rad upphör. Skilj mellan att en rad försvinner ur exporten och att dess geografi formellt övergår till ett annat område. Ändra inte historiska medlemskapsår enbart utifrån att områden är grannar eller att arealer råkar summera exakt.
