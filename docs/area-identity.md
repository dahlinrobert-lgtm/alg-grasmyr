# Områdesidentiteter: Gräsmyrs VVO och Hörneåns ÄSO

## Grundregel

Behandla dessa som separata geografiska enheter tills Länsstyrelsens områdesregister, ID:n och gränser visar hur de hänger ihop.

- **Gräsmyrs viltvårdsområde** är den historiska identitet som ska sökas i äldre statistik. Statistikportalens områdeslista visar `24-01-02-017-A - GRÄSMYRS VILTVÅRDSOMRÅDE`, internt `AjoId=718148`.
- **Hörneåns älgskötselområde** är den nuvarande/större förvaltningsidentitet som ska sökas i den moderna statistiken. Statistikportalens områdeslista visar `24-01-02-342-Ä - Hörneåns älgskötselområde`, internt `AjoId=724577`. Båda finns under **Sydöstra älgförvaltningsområdet** och är två skilda val i portalens jaktområdeslista (verifierat 2026-10-17).

Ett äldre lokalt jaktområde/VVO kan vara en del av ett senare ÄSO utan att de har samma gräns eller omfattning.

## Historiskt sökspår (inte verifierat)

En sekundär återgivning av en tabell med rubriken *Älgtilldelning 2012* listar:

- Namn: Gräsmyrs viltvårdsområde
- Områdesbeteckning: `01-02-017`
- Areal: cirka 4 795 ha

Källa: [återgivning av Älgtilldelning 2012](https://www.yumpu.com/sv/document/view/27615173/pdf-dokument-algtilldelning-2012-svt).

Detta är **endast en ledtråd för sökning**. ID, areal, status och koppling till nuvarande jaktområden måste verifieras mot Länsstyrelsens officiella WebbGIS/statistikportal. Tilldelningstal i den historiska tabellen är inte samma sak som faktiskt fällda älgar och ska inte läggas in i avskjutningsserien.

## Verifiering i primärkällan

1. Öppna [Älgdata WebbGIS](https://ext-webbgis.lansstyrelsen.se/lst_algdata/).
2. Sök efter både Gräsmyrs viltvårdsområde och Hörneåns älgskötselområde.
3. Anteckna officiellt ID, områdestyp, beslut/status, giltighet och area.
4. Kontrollera om det finns historiska gränser och notera om Gräsmyr ingår i det nuvarande ÄSO:t eller om gränserna avviker.
5. Upprepa kontrollen i [statistikportalen](https://algdata-apps.lansstyrelsen.se/algdata-apps-stat/) genom att växla mellan historiska och nuvarande gränser.

Registrera resultatet i `data/area_registry.csv`. Ändra inte till verifierad status utan en primärkälla.


## Result of later-period test (2026-10-17)

The download workflow tested Gräsmyrs portal ID `718148` for 2020/2021–2025/2026 using both the current-boundary selector and the historical-boundary selector. Neither returned the Gräsmyrs area as a selectable option under Sydöstra ÄFO. The separate 2010/2011–2019/2020 query returned actual rows only for 2010/2011–2012/2013.

This establishes a **coverage break in this report/area selection**, not that harvest was zero after 2012/2013. To establish continuity, use Länsstyrelsen's historical area register/decisions or ask the county board whether Gräsmyrs VVO's reporting was moved to a new ÄJO/ÄSO identity and from which hunting year. Do not append Hörneåns ÄSO totals to Gräsmyrs VVO as though they were the same geographic unit without this evidence.
