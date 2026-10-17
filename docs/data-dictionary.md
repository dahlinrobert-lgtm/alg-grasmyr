# Data dictionary – älgstatistik

Detta är ett preliminärt schema. Kolumner ska mappas från riktiga exportfiler när dessa har hämtats från Älgdata; hitta inte på saknade värden.

| Fält | Beskrivning |
|---|---|
| `area_name_source` | Områdesnamn exakt som det står i källan |
| `area_id` | Områdets officiella ID om det finns i källan |
| `area_name_normalized` | Normaliserat områdesnamn för sökning, exempelvis Gräsmyrs viltvårdsområde eller Hörneåns älgskötselområde |
| `hunting_year` | Jaktår enligt källan, bevara originalformatet |
| `statistic_type` | Statistiktyp enligt källan, exempelvis avskjutning eller älgobs |
| `indicator` | Variabel/indikator enligt exporten |
| `value` | Numeriskt värde om det kan tolkas säkert |
| `unit` | Enhet, om den finns i källan |
| `sex_age_group` | Köns-/åldersgrupp om exporten innehåller den |
| `source_url` | URL till statistikportalen eller karta |
| `retrieved_at_utc` | Tidpunkt då filen hämtades |
| `source_file` | Ursprungligt filnamn |
| `notes` | Anmärkningar om saknade värden, definitioner eller ändrad geografi |

## Viktiga kvalitetsregler

- Behåll alltid originalexporten och ändra den inte.
- Saknade värden ska förbli saknade, inte bli noll.
- Jaktår är inte kalenderår; lagra dem som text tills formatet är verifierat.
- Dubbletter ska identifieras med områdes-ID, jaktår, statistiktyp, indikator och eventuella dimensioner från källan.
- Om ett områdes namn eller geometri ändras, lagra namn-/ID-historik och dokumentera om tidsserier är jämförbara.
