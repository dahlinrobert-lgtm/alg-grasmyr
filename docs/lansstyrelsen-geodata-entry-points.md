# Geodatakällor för älgjaktsområden – Länsstyrelsens direkta ingångar

## Sammanfattning

Geodatakatalogens metadata-ID `6d4c42de-2b43-4b72-98ec-856d8adfaf29` identifierar datamängden **LST Älgjaktsområden**. Det är en viktig ny ingång till projektet eftersom den innehåller geodata för beslutade älgjaktsområden som polygoner, inte bara arealer i statistikrapporter.

Källa: [Länsstyrelsernas metadata för LST Älgjaktsområden](https://ext-geodatakatalog.lansstyrelsen.se/GeodataKatalogen/srv/api/records/GetMetaDataById?id=6d4c42de-2b43-4b72-98ec-856d8adfaf29)

## Direkt identifierade resurser

| Resurstyp | URL | Användning |
|---|---|---|
| ArcGIS Map Service | [lst_jaktadm_visning/MapServer](https://ext-geodata-applikationer.lansstyrelsen.se/arcgis/rest/services/Jaktadm/lst_jaktadm_visning/MapServer) | Fråga lagrens metadata, attribut och geometrier via ArcGIS REST |
| WMS | [lst_jaktadm_visning/WMSServer](https://ext-geodata-applikationer.lansstyrelsen.se/arcgis/services/Jaktadm/lst_jaktadm_visning/MapServer/WMSServer) | Visa polygonerna i QGIS/ArcGIS eller annan WMS-klient |
| Nedladdningsbar Shape-export | [LST_jaktadm_ajo_afo.zip](https://ext-dokument.lansstyrelsen.se/gemensamt/geodata/ShapeExport/LST_jaktadm_ajo_afo.zip) | Hämta områdespolygoner och attribut för lokal analys |
| Älgdata-WebMap från användarens export | [LST Älgdata – WebMap](https://ext-geoportal.lansstyrelsen.se/arcgis/home/item.html?id=719131c7985849e3a17d429d41be7c7a) | Kartkonfiguration som användarens lagerlista pekar på |

## Vad metadata säger

- Datamängden beskriver Länsstyrelsernas publika geodata för **beslutade älgjaktsområden**, uppdelade i licensområden och älgskötselområden.
- Geometrierna är vektordata; ArcGIS-tjänsten anger polygoner.
- Referenssystemet är **SWEREF 99 TM (EPSG:3006)**.
- Metadata anger uppdatering från JaktAdm. och att ett nytt beslut blir synligt publikt dagen efter.
- Datamängden innehåller huvudsakligen beslutad landareal, områdesnummer, områdestyp och senaste beslutsdatum.
- Användningsrestriktionen anges som **CC0 1.0** och åtkomst som utan begränsning.
- Tjänstens lagerlista anger:
  - lager 0: **LST Älgjaktområden**
  - lager 1: **LST Älgförvaltningsområden**
  - lager 2: **LST Kronhjortsskötselsområden**

Metadata listar attribut som bland annat `NAMN_AJO`, `NAMN_AFO`, `AFO_ID`, `BSLAREA_HA` och `BESLUTDAT`. Det gör det möjligt att söka efter områdesnamn och beslutade arealer och att jämföra den registrerade arealen med Excel-serien.

## Relevans för Gräsmyr och Hörneåns

Det här är en bättre källa för att kontrollera **nuvarande beslutade polygoner** och deras attribut. Nästa konkreta analys är att hämta lagrets attribut och geometrier och söka efter namn/ID kopplade till Gräsmyr, Hörneåns, Öre-Brattfors och Hallens.

### Viktig begränsning: detta är inte automatiskt en historisk gränsdatabas

Metadata beskriver den aktuella publika datamängden och dess uppdateringsfrekvens. Den lovar inte att alla tidigare polygonversioner finns tillgängliga. Därför gäller:

1. En matchande aktuell polygon kan bekräfta nuvarande geometri och attribut.
2. En matchning mellan aktuell polygon och äldre Excel-areal är en kontrollpunkt, inte ensam ett bevis på att samma polygon gällde historiskt.
3. För att fastställa när ett område ändrades behöver vi äldre geodata, beslutshistorik eller uttryckliga uppgifter i myndighetsmaterialet. Vi ska inte härleda ett formellt datum enbart från arealsummor.

## Lagerlistan som användaren skickade

Den uppladdade CSV-filen `toc_export_20261018_083840.csv` innehåller fem poster, alla av typen `ArcGISFeatureLayer`, kopplade till samma WebMap:
- Älgjaktsområden
- Älgjaktsområden – Licensområden
- Älgjaktsområden – Älgskötselområden
- Kronhjortsskötselsområden
- Älgförvaltningsområden

Det visar vilka lager som ingår i kartkonfigurationen, men CSV:n innehåller inte själva polygongeometrierna eller lager-URL:erna. För geometrierna ska vi använda REST-tjänsten eller Shape-exporten ovan.

## Nästa arbetsordning

1. Inspektera attributschemat för lager 0 och fråga efter poster där områdesnamn eller områdesnummer matchar de aktuella sökorden.
2. Hämta relevanta polygoner som GeoJSON eller shapefile.
3. Kontrollera aktuell polygonarea och geometri i EPSG:3006.
4. Jämför endast som separat evidens med Excel-historiken; märk inte historiskt medlemskap bekräftat utan historiska gränser eller beslutsstöd.


## Alternativ geodatakälla: viltvårdsområden (VVO)

En separat Länsstyrelse-publicerad ArcGIS Feature Layer finns för **LstZ Viltvårdsområden**:

- [REST-lager 8 – LstZ Viltvårdsområden](https://ext-geodata-lokala.lansstyrelsen.se/arcgis/rest/services/LSTZ/lstz_extern_jakt2/MapServer/8)
- [Metadata för viltvårdsområden](https://ext-geodatakatalog.lansstyrelsen.se/GeodataKatalogen/srv/api/records/GetMetaDataById?id=73d176e7-ba23-4656-8123-a5bbb5a2f603)

REST-sidan anger polygongeometri, EPSG:3006 och fälten `Namn`, `VVO` och `AREA_HA`. Det är en annan datamängd än beslutade älgjaktsområden och därför en potentiellt relevant väg för att hitta geometri för äldre eller nuvarande viltvårdsområden som Gräsmyrs VVO.

**Viktig korrigering efter kontroll av tjänstens utbredning:** lagrets utbredningsrektangel är X 388 328–585 694 och Y 6 834 307–7 184 827 i EPSG:3006. Den ligger väster om Gräsmyr/Umeå-området och omfattar inte målområdet i Västerbotten. Därför är detta lager inte en lämplig källa för Gräsmyrs polygon, även om attributschemat är relevant som exempel på hur Länsstyrelsen publicerar VVO-data. Vi ska inte lägga tid på att söka Gräsmyr i just denna regionala tjänst. En separat Västerbottenskälla behöver identifieras. Även om en liknande VVO-polygon hittas i en annan tjänst är en aktuell geometri inte i sig historisk gränsbevisning.

Den här källan bör undersökas parallellt med `LST Älgjaktsområden`: den ena avser VVO-polygoner, den andra beslutade älgjaktsområden.


## Status för VVO-lagret i den här analysen

REST-metadata för [LstZ Viltvårdsområden, lager 8](https://ext-geodata-lokala.lansstyrelsen.se/arcgis/rest/services/LSTZ/lstz_extern_jakt2/MapServer/8) anger extent i EPSG:3006: X 388 328–585 694, Y 6 834 307–7 184 827. Det geografiska intervallet täcker inte Gräsmyr/Umeå-området. Lagret har därför klassats som **regionalt sidospår – inte relevant geometri för målområdet**. Nästa steg är att hitta motsvarande VVO-data för Västerbotten eller att använda den länsövergripande tjänsten för beslutade älgjaktområden.


## Extern historisk ledtråd (inte primärkälla)

En webbsökning hittade en återpublicerad sammanställning med rubriken **”Älgtilldelning 2012”**. Den listar bland annat Gräsmyrs VVO (4 795 ha), Öre-Brattfors VVO (3 151 ha), Hallens VVO (1 553 ha), Djupsjö VVO (2 506 ha), Nyåkers VVO (2 568 ha), Mullsjö VVO (3 492 ha), Tallbergslidens VVO (3 172 ha), Hörnsjö VVO (6 601 ha), Hummelholms VVO (5 508 ha) och Torrböle VVO (3 209 ha). En separat återpublicerad gästbokstråd från 2012 nämner ett nytt älgskötselområde och anger att Hörnsjö, Gräsmyr, Mullsjö, Torrböle, Hummelholm och Tallberg skulle delta.

Källor:
- [Återpublicerad ”Älgtilldelning 2012”](https://www.yumpu.com/sv/document/view/27615173/pdf-dokument-algtilldelning-2012-svt)
- [Hörnsjö VVO:s återpublicerade gästbok](https://www3.olzzon.com/g/g.php?a=s&i=g32-03680-34&m=alla&p=1)

**Bevisvärde:** detta är en sekundär webbkopia, inte ett officiellt originalbeslut och inte polygondata. Den fungerar som sökledtråd för att hitta äldre tilldelningslistor eller beslut hos Länsstyrelsen, men ska inte ersätta de officiella Älgdata-Excelutdragen. Den antyder att flera av de lokala områdena redan 2012 kopplades till ett nytt ÄSO, men fastställer inte exakt geometri, datum för registreringsändring eller om alla gränser var identiska.

## Nästa geodatasteg

Länsstyrelsens officiella information för Västerbotten beskriver tre former av älgjakt: registrerat älgskötselområde, registrerat licensområde och oregistrerad mark. Den hänvisar till Länsstyrelsens geodatakatalog som ingång till länsvisa och rikstäckande data. Se [Älgförvaltning och jaktområden – Västerbotten](https://www.lansstyrelsen.se/vasterbotten/djur/jakt-och-vilt/algjakt/algforvaltning-och-jaktomraden.html) och [Kartor och geodata – Västerbotten](https://www.lansstyrelsen.se/vasterbotten/om-oss/vara-tjanster/kartor-och-geodata.html).

I nuläget har vi en användbar officiell tjänst för dagens beslutade älgjaktområden, men ingen verifierad historisk VVO-polygon för Gräsmyr. Nästa avgörande källa vore ett äldre beslut/bilaga med karta eller en arkiverad version av polygonlagret.


## Traktnamn i fastighetsbeteckningar – sökstrategi för Nordmaling

Målet är att använda traktledet i fastighetsbeteckningar som en söknyckel för att hitta handlingar om de historiska viltvårdsområdena. En fullständig beteckning består normalt av kommun/registerområde, trakt, block och enhet; exempelvis kan den skrivas `Nordmaling Gräsmyr 15:1`. Traktnamnet är inte i sig en juridisk gräns för ett älgjaktsområde.

### Traktnamn med direkt officiellt belägg i Nordmaling

| Traktled / namn | Vad källan bekräftar | Evidens |
|---|---|---|
| Gräsmyr | Länsstyrelsens beslut om Hörnån naturreservat listar fastigheten Gräsmyr 15:1 i Nordmalings kommun. | Direkt exempel på fastighetsbeteckning |
| Mullsjö | Samma beslut listar flera Mullsjö-fastigheter i Nordmaling, bland annat 1:13, 1:14, 1:21, 1:22 och fler. | Direkt exempel på fastighetsbeteckningar |
| Hörnsjö | Länsstyrelsens beslut om Rötjärnbergets naturreservat listar Hörnsjö 2:40, 2:74 och 3:72 i Nordmaling. | Direkt exempel på fastighetsbeteckningar |

Källor: [Hörnån naturreservat, beslut 2019](https://www.lansstyrelsen.se/download/18.6585fd516e4501062871a34/1574932728179/24FS%202019-24%20H%C3%B6rn%C3%A5n%20naturreservat.pdf) och [Rötjärnbergets naturreservat, beslut 2025](https://www.lansstyrelsen.se/download/18.1a7d70ab19a0a379be476c/1761119496660/R%C3%B6tj%C3%A4rnbergets%20naturreservat_Beslut20251021us.pdf).

### Kandidater att testa mot fastighetsregistret

Utifrån de historiska områdesnamnen i Excel-registret ska nästa sökning testa följande traktled: `Gräsmyr`, `Mullsjö`, `Hörnsjö`, `Hummelholm`, `Torrböle`, `Tallberg`, `Nyåker`, `Djupsjö`, `Öre-Brattfors` och `Hallen`. Detta är en **söklista**, inte en bekräftelse på att varje namn förekommer som trakt i Nordmalings fastighetsregister; vissa kan vara bynamn, äldre områdesnamn eller ligga i annan kommun/registerindelning.

### Viktig metodbegränsning

Lantmäteriets öppna Min karta kan visa fastighetsgränser och fullständig fastighetsbeteckning när man zoomar in, men kartans fastighetsgränser är uttryckligen inte juridiskt gällande. Fastighetsregistrets uppgifter om nuvarande och tidigare beteckningar samt fastighetsrättsliga åtgärder kan vara relevanta för historik. För att fastställa vilka fastigheter som ingick i ett jaktområde krävs dock helst Länsstyrelsens registreringsbeslut med fastighetsförteckning och kartbilaga.

Länkar: [Lantmäteriet – hitta fastighetsbeteckning i Min karta](https://www.lantmateriet.se/sv/kartor/vara-karttjanster/min-karta/hitta-fastighetsbeteckning-i-min-karta/) · [Lantmäteriet – fastighetsregistrets innehåll](https://www2.lantmateriet.se/sv/fastighet-och-mark/information-om-fastigheter/Fastighetsregistret/registrets-innehall/).

### Rekommenderad fortsättning

1. Samla officiella beslut och kartbilagor för Gräsmyrs VVO och Hörneåns ÄSO.
2. Extrahera varje fastighetsbeteckning ur beslutsbilagorna och normalisera kommun, trakt, block och enhet.
3. Gruppera listan efter trakt och jämför den med Excel-arealerna per säsong.
4. Märk varje resultat som direkt dokumenterat, namnlikhet eller ännu obekräftad hypotes. Använd inte enbart traktledet för att tilldela en fastighet till ett historiskt jaktområde.
