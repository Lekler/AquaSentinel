# AquaVerify, water bodies and observed persistence

These transparent experimental rules do not classify locations as risk, authenticate reports or predict environmental events.

## Registration and identification

The authenticated team registers standardized water body names in the map review area. The database assigns permanent internal codes such as `WB-BG-001`. These are not official codes or geographic boundaries. Include the municipality/segment to distinguish names. Normalization avoids duplicates differing only in case, accents or spaces.

Participants select a code or Unidentified. The free-text location describes the point. The team confirms or updates the linkage, recording the responsible person, date and previous ID. Groups require a confirmed water body code and proximity within 200 m of the anchor. Unconfirmed reports remain separate, even with identical names. Names do not trigger automatic migration. The catalogue must use the same persistent PostgreSQL database as reports.

## AquaVerify v1

The 0–100 index measures documentary completeness and quality, not the probability that a report is true. High ≥75; medium ≥45; low <45. It is not calibrated.

| Criterion | Maximum | Rule |
|---|---:|---|
| Valid image | 20 | Server-decoded and validated file |
| Resolution | 10 | Shortest side ≥480 px: 10; ≥240 px: 5; otherwise: 0 |
| Detection | 10 | At least one recognized object; no detection does not invalidate the report |
| AI confidence | 15 | Average detection confidence ×0.15 |
| Location | 10 | Confirmed browser GPS: 10; manual/adjusted: 3 |
| GPS accuracy | 5 | Up to 50 m: 5; up to 200 m: 2; absent/worse: 0 |
| Duplication/similarity | 10 | Complete index, informative image and no pending match |
| Date/time | 5 | Server-recorded submission; optional EXIF gives no bonus |
| Human review | 15 | Team validation |

GPS and EXIF are reported metadata, not proof of capture place/time. Adjusting coordinates removes the GPS contribution. Missing legacy evidence scores zero for that criterion; information is not invented.

## Image similarity

SHA-256 detects identical input images. pHash compares perceptual signatures, including predefined crops, to flag possible similarity after resizing, recompression and small changes. It can miss major crops, rotations or edits and can flag different but visually similar scenes. It does not authenticate images or prove fraud.

Older photos can be indexed in batches in the team area. No photo is deleted automatically. The team compares evidence and records an independent-observation or reused-image decision with a reason. Pending or reused similarities do not increase WPS frequency or persistence.

References: [pHash design](https://phash.org/docs/design.html), [perceptual hashing](https://phash.org/docs/howto.html), [Pillow](https://pillow.readthedocs.io/en/stable/reference/Image.html).

## Persistent hotspot v1

The fixed 90-day window is independent of map filters. Eligible evidence requires public validated reports, a confirmed water body, AquaVerify ≥60, an informative pHash, complete historical comparison and no pending/reused similarity. Identical SHA-256 values count once. This does not establish independent authorship.

Each Brasilia calendar day has one vote: its latest eligible report. All criteria must be met:

1. At least three distinct days with reported waste.
2. At least 14 days between the first and latest waste observation days.
3. Waste on at least 60% of eligible observed days.
4. Median WPS ≥50 on days with waste, recalculated at each report date.
5. Median AquaVerify ≥60.
6. The latest public report is eligible, still shows waste and is at most 30 days old.
7. A single confirmed water body in the segment.

No badge does not mean no problem. More reports do not mean more pollution. Dates are submission dates; observed persistence is not continuous monitoring.

## Explanation and human review

Screens and the AquaVerify spreadsheet explain counts, average confidence, low confidence (<60%), intermediate confidence (<80%), detection limits, coordinates, water body identification and similarity issues. Overlapping boxes with IoU >0.55 are removed, retaining the most confident box within each photo. This does not identify unique objects across photographs. All reports require human review before publication.
