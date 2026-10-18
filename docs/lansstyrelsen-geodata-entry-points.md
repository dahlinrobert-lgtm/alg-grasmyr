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
