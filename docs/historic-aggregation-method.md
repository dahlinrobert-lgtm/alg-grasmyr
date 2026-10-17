# Metod för historisk arealavstämning – endast officiella Excel-exporter

## Källregel

Den här dokumentationen använder endast myndighetens publicerade Excel-exporter från Älgdata som belägg för statistik, rapporterad areal, registreringsnummer, områdesnamn och förekomst per jaktår. Externa listor, lokala jaktlagskällor, nyhetsartiklar och andra webbplatser ska inte användas för att komplettera eller förklara statistiken.

CSV-filer och webbplatsens tabeller är bearbetade representationer av Excel-uppgifter. Vid konflikt ska original-Excel-filen kontrolleras och den bearbetade filen rättas. Behåll den rapporterade arealen med källans precision.

## Tillgängliga säsonger

Inventeringen av original-Excel visar följande täckning:

- **Nuvarande gränser:** 2000/2001–2026/2027.
- **Historiska gränser:** 2012/2013–2026/2027.
- **2017/2018 och 2018/2019:** båda exporttyperna finns tillgängliga och har jämförts per registreringsnummer.

För 2000/2001–2011/2012 finns endast exporter för nuvarande gränser. För 2012/2013–2026/2027 finns både historiska och nuvarande gränser. Jämförelsen för 2017/2018 och 2018/2019 visar identiska registreringsnummer och registrerade fält mellan exporttyperna.

## Regler för jämförelser

1. Jämför registreringar med registreringsnummer, inte radposition.
2. Bevara rapporterat områdesnamn och areal som de står i Excel.
3. Beräkna arealförändringar från rapporterade totalarealer och redovisa beräkningen separat från källvärdet.
4. En summa som exakt motsvarar en förändring är endast en aritmetisk matchning. Den visar inte i sig medlemskap, överföring eller identiska gränser.
5. Att en separat registrering saknas i en senare tillgänglig export betyder endast att den inte återfinns separat i den filen. Det bevisar inte när eller varför registreringen försvann.
6. Skilj mellan verifierat direkt Excel-värde, beräknad differens och en obekräftad tolkning. Ingen tolkning ska presenteras som myndighetsstatistik.

## Observerade arealvärden

Hörneåns rapporterade arealserie i Excel börjar 2013/2014 med 26 777 ha. De rapporterade förändringarna är:

| Jaktår | Rapporterad areal | Förändring från föregående redovisade jaktår |
|---|---:|---:|
| 2013/2014 | 26 777 ha | Basår |
| 2014/2015 | 32 355 ha | +5 578 ha |
| 2015/2016–2016/2017 | 32 355 ha | Ingen rapporterad förändring i tillgängliga Excel-exporter |
| 2017/2018 | 32 355 ha | Ingen rapporterad förändring |
| 2018/2019 | 35 506 ha | +3 151 ha |
| 2019/2020 | 35 506 ha | Ingen rapporterad förändring |
| 2020/2021 | 35 567,05 ha | +61,05 ha |
| 2021/2022–2022/2023 | 35 567,05 ha | Ingen rapporterad förändring |
| 2023/2024 | 37 132,8 ha | +1 565,75 ha |
| 2024/2025–2025/2026 | 37 132,8 ha | Ingen rapporterad förändring |

Observera att tabellen visar de rapporterade arealvärdena och differenserna. Den fastställer inte orsaken till förändringarna eller geografisk kontinuitet.

## Registreringar som behöver beskrivas försiktigt

- **Öre-Brattfors:** separat registrering på 3 151 ha i Excel-exporterna till och med 2017/2018 och saknas som separat rad i 2018/2019. Hörneåns rapporterade areal ökar med 3 151 ha samma säsong. Detta stödjer ett samband men fastställer inte formellt medlemskap eller identiska gränser.
- **Hallens:** separat registrering på 1 567,62 ha i Excel 2021/2022 och 2022/2023. Hallens saknas som separat rad i tillgängliga exporterna från 2023/2024. Hörneåns rapporterade förändring det året är 1 565,75 ha, en skillnad på 1,87 ha. Detta fastställer inte medlemskap eller identiska gränser.
- **2020/2021:** förändringen är 61,05 ha. Ingen motsvarande separat registrering har identifierats i den granskade Excel-serien. Orsaken är okänd; kalla den inte felinmatning och anta inte en områdesanslutning.
- **Namnlös registrering 24-01-02-183-A:** Excel visar en tom områdesnamnsuppgift och rapporterad areal på 504 ha under 2010/2011–2012/2013. Koppla inte registreringen till ett annat områdesnamn utan stöd i Excel.

## Granskningsfiler

- [Registreringshistorik för historiska och nuvarande gränser](../data/processed/area-registration-boundary-audit.csv)
- [Sammanfattning av jämförelse mellan gränsexporter](../data/processed/boundary-comparison-summary.md)
- [Direkt kontroll av Hörneåns rapporterade areal](../data/processed/hornean-area-source-check.csv)
- [Säsongsvis arealavstämning](../data/area_reconciliation_by_season.csv)
- [Arealrelationer och kandidatmatchningar från Excel](../data/historical_area_crosswalk_candidates.csv)

Dessa filer är bearbetningar av de ursprungliga Excel-exporterna och ska kunna spåras tillbaka till säsong och registrering. De är inte självständiga bevis för medlemskap eller geografiska gränser.
