# Källavstämning inför nationell insamling

Myndighetens Excel-exporter är primärkälla. Lägg originalfiler under \`data/raw/\` (eller säkra åtkomsten via ett separat arkiv); deklarera varje fil i \`data/source_exports/manifest.json\`. En deklaration måste innehålla unikt \`source_id\`, \`relative_path\`, \`sha256\`, \`area_key\`, numeriskt portal-\`area_id\`, \`hunting_seasons\`, \`report_id\`, \`boundary_mode\` och \`exported_at_utc\`.

Kör \`python scripts/verify_source_exports.py\`. Resultatet hamnar i \`data/quality/source_export_audit.json\` och som GitHub Actions-artifact. Saknad fil, felaktig kontrollsumma och ogiltig deklaration ger felstatus. Ett tomt manifest passerar, men betyder **noll verifierade originalexporter**.

**Viktig skillnad:** \`integrity_verified\` bekräftar att filen finns och har deklarerad SHA-256. Det betyder inte att dess cellvärden överensstämmer med portalens snapshots. Kandidatkoppling på område och rapport är endast metadata. Full värdeavstämning kräver separat parser och verifierad fältmappning för originalformatet; ingen sådan kontroll påstås här.

Nationell utbyggnad ska föregås av geografiskt spridningstest där identiteter, gränsläge, jaktår, rapporttyp, täckning och avvikelser kontrolleras separat per område.
