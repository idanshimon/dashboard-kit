# Sensor-map measurements: decode, derive, and display

## 1. Identify the subject and preserve evidence

Match the active device using its actual account identifier and internal model, not its marketing name. Record acquisition time separately from map-generation time. Preserve original encoded bytes and hashes; keep retired-device captures as explicitly historical fixtures rather than overwriting their identity.

Prefer cached map/file reads over refresh or motion commands. Successful cloud discovery is not evidence that an existing integration switched to the replacement. Keep source maps, identifiers, signed URLs and network metadata private; a shareable viewer should embed only needed geometry and non-secret provenance.

## 2. Test existing decoders against real bytes

Inspect maintained parser implementations and fixtures before writing a decoder. Relevant Dreame examples include Tasshack/dreame-vacuum, Hypfer/Valetudo (DreameMapParser and the Kaitai dreame_map_file specification), and PiotrMachowski/Python-package-vacuum-map-parser-dreame. A renderer of already-decoded Valetudo JSON is not a native backup parser. Pin the inspected revision and check its license before reuse.

Check each actual payload independently: an embedded app frame, an app_map binary, a fine-map binary and a tiled map extension can all be different formats within one backup. Do not declare full parser compatibility after testing only a header. Do not treat zero indexed search results as proof that no decoder exists.

### Known app-frame structural probe

Some saved app frames use URL-safe base64, then zlib, a 27-byte header, a byte-per-cell image and trailing JSON. After strict decoding and bounded decompression:

```python
pixel_mm, width, height, left_mm, top_mm = struct.unpack_from('<5h', decoded, 17)
assert pixel_mm > 0 and width > 0 and height > 0
end = 27 + width * height
assert end <= len(decoded)
metadata = json.loads(decoded[end:])
```

Validate the frame marker and supported version too. Use the appropriate upstream pixel decoder: bit layouts differ by version; raw nonzero bytes cannot simply be counted as floor. Upstream normalized pixel arrays may be indexed `[x][y]` even when serialized cells are row-major.

### Encoding and binary-structure gates

- Sniff archive magic rather than trusting Content-Type: a response labeled gzip can contain bzip2. Extract only bounded regular members, rejecting traversal, absolute paths and links.
- Use `base64.b64decode(value, altchars=b'-_', validate=True)` where the source uses the URL-safe alphabet. Never discard a supposedly stray character to force decoding; permissive decoding can corrupt data while still yielding plausible record lengths.
- Require declared record count, byte coverage, unique coordinates and histograms to reconcile before interpreting a custom container.
- For `NEWMV001_RI_V001` YXMap extensions, an observed structure is a 16-byte prefix, five little-endian uint32 fields, one byte, then N records of two bytes plus 1024 payload bytes. Treat proposed 32×32 tile placement and coordinate strides as hypotheses until aligned with known geometry or source code.
- A layer named `reuse_lds_height_map` with values such as 0/1/3 may encode flags or coarse height classes. Neither continuous elevation nor absence of all height information follows from that histogram. Keep units and semantics unknown until proven.

## 3. Calculate the quantities that are actually available

Persist one batch of per-room results, then aggregate that file programmatically and reconcile room IDs against source metadata.

- **Mapped floor area:** count unique decoded floor cells belonging to each room, excluding wall/obstacle codes; multiply by `(pixel_mm / 1000) ** 2`. This may omit furniture and inaccessible space.
- **Outline area:** validate closed, ordered, non-self-intersecting room polygons; use shoelace area or a geometry library. Robot-generated outlines can bridge unobserved space and are not necessarily surveyed wall boundaries.
- **Room extents:** report `max(x)-min(x)` and `max(y)-min(y)` as maximum XY extents. Do not imply their product equals usable area for an irregular room.
- **Combined area:** compute polygon union and compare with the sum. For proven rectilinear polygons, integrate occupancy over slabs defined by every unique vertex X/Y; test each slab midpoint against all polygons. For arbitrary polygons use a robust geometry library. Report overlaps rather than silently double-counting.
- Convert units explicitly: `sqft = m2 / 0.09290304`. Round for presentation only; preserve full precision and provenance in the artifact.

Distinguish mapped rooms from the entire building. A unit-bearing coordinate scale allows an estimate immediately; calibration with physical wall distances is a later accuracy check, not a prerequisite to doing the arithmetic.

## 4. Render useful output while deeper decoding continues

Produce a real 2D plan from known geometry before letting proprietary-binary research dominate the task. Offer mapped cells and simplified outlines as separate views, with room names from the source marked as robot-assigned.

A portable 3D preview can extrude those polygons in an offline HTML canvas with orthographic projection, depth-ordered wall faces, drag orbit, zoom and cutaway controls. Distinguish conceptual extrusion from measured XYZ data. Subtract door spans only after checking collinearity and overlap; without measured opening heights, label full-height gaps as simplified openings rather than inventing lintels. A single pixel/file-size test does not verify the rendering.

Track vertical inputs individually as assumed, user-confirmed or sensor-measured. Regenerate visible badges, labels and exported HTML when the user confirms a default; keep adjustable deviations labeled hypothetical. Do not silently assign the height to other levels or rooms with different ceilings.

Verify the exact attachment via file:// with network disabled, at desktop and narrow mobile widths. Exercise height changes, cutaway, label toggle, pointer drag, zoom and reset/top view; inspect screenshots for fit, room readability and wall joins. Deliver the HTML file itself when requested, not only a path or screenshot.
