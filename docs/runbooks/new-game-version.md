# Runbook: Konami Releases a New DDR Game Version

Steps to take when Konami releases a new arcade version (e.g. A3 → WORLD). This list is incomplete; add steps as you discover them.

For reference, WORLD's release was handled by migrations `0144` (Version row) and `0148` (moving Cabinets and UnlockEvents to the new version).

## Checklist

1. **Add the Version row** for the new game version.
2. **Update Cabinets**: move existing Cabinets to the new Version, and add or retire Cabinets for each Region. The `scores` view expects exactly one white Cabinet per Region and exactly one gold Cabinet.
3. **Point existing UnlockEvents at the right Version**, where they carry over into the new game.
4. **Update hard-coded version ids**: `version_id=20` appears in `scorebrowser/views.py` (Synchronization's unknown-chart discovery, admin Unlock views, the Unlock admin page). Remove this step once [#67](https://github.com/rrwoods/pprx/issues/67) is resolved.
5. **Re-check the A3+ region exception**: decide whether the `New Challenge charts (A3+)` UnlockTask still describes which charts are unplayable in the A20PLUS-only region. Remove this step once [#66](https://github.com/rrwoods/pprx/issues/66) is resolved.
6. **Re-export the test Base Data fixture** from a local copy of production, so tests see the new Version and Cabinet layout (ADR-0006):
   ```bash
   python pprxweb/manage.py dumpdata scorebrowser.Difficulty scorebrowser.Version scorebrowser.Region scorebrowser.Cabinet scorebrowser.CabinetModel scorebrowser.ProfileVisibility --indent 2 -o pprxweb/scorebrowser/fixtures/basedata.json
   ```
