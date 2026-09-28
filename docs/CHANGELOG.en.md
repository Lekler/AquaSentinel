### 2026.09 · Postal codes, addresses and returning to the map

- Map and Reports is the first shortcut, before Monitoring, Coverage gaps and Track a report.
- Explicit postal-code/address search with suggestions for photo reports and planned segments.
- GPS and adjustable maps retained; manual coordinates collapsed.
- Separate report/segment state, cached searches and graceful service failures.
- Public URL unchanged; details in ENDERECOS.md.

### 2026.09 · Map and contrast fix

- Replaced the CARTO endpoint displaying “API key required” with an Esri street basemap verified using an actual Rio map image.
- Report form, public map and coverage gaps share the same source; map style served by the app.
- Darker helper text, captions and instructions; 8.6:1 contrast on the main light background.
- Marker, GPS accuracy, zoom and persistent map updates retained.

### 2026.09 · Simple reporting and team review

- Voyager basemap, persistent Leaflet instance and GPS circle only when accuracy is available.
- Concise public results with count, classes and confidence when detections exist.
- Technical record details restricted to the authenticated team; history and exports retained.
- Explicit sign-in and sign-out, one-hour sessions invalidated by password changes.
- Sequential review with one main image and optional original view.
- Editable water body names, types and notes with stable IDs and duplicate prevention.
- Additive water body metadata table; existing records preserved.

### 2026.09 · Navigation, map clarity and languages

- Concise location summaries; persistence details are collapsible.
- Review tasks grouped with one responsible-person field.
- Level legends use a single colored marker with text.
- Data and science and Transparency in the top-right menu.
- Illustrated tutorial in How it works; Contact us is part of Questions.
- Smaller home buttons and more spacing.
- English UI catalogue, persistent language selection and translated GPS messages.
- User-provided names, notes, original photos and stored scientific identifiers retain their original content.

### 2026.09 · Photo results

- Restored colored level buttons without extra symbols or a duplicate legend.
- Saved-location card, AquaVerify score bar and per-criterion table.
- Grouped explanations, private receipt, actions and downloads.

### 2026.09 · Open science

- About, Questions, environmental context and safety notice.
- CSV, Excel, JSON and GeoJSON exports with authorization and data dictionary.
- Internal `aqua-observation-v1` profile inspired by SensorThings.
- New reports store WPS v1, CS v1 and AquaVerify v1; legacy versions are not invented.

### 2026.09 · Monitoring and evidence

- Transparency, structured sessions, coverage gaps, receipts and lifecycle.
- Actions and descriptive before/after comparisons.
- Water body codes, AquaVerify, SHA-256, pHash and persistent hotspots.
