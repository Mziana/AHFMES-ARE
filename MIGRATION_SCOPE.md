# ARE extraction scope

## Included

Exactly 228 byte-preserved files from source commit
`dcecafd1f9caae130da3880170f018026b1d5183`:

- 215 `PROJECT_GOVERNANCE/AHFMES_ARE*` documents;
- 4 legacy `AHFMES_AUTONOMOUS_RESEARCH_ENGINE*` documents;
- `PROJECT_GOVERNANCE/CURRENT_AUTHORITY_INDEX.md`;
- 8 ARE-only diary records.

## Deliberately excluded

- All Condition Atlas and Position Path Replay implementation, data, and
  generated evidence.
- Production/runtime code, tests, dashboards, research folders, and agent
  memory.
- `PROJECT_JOURNAL/DIARY/2026-08-20-PPR-G1-CLOSURE-AND-ARE-DIRECTION.md`, which
  mixes PPR and ARE content.
- `PROJECT_JOURNAL/STATUS/CURRENT_RESEARCH_STATUS_2026-08-20.md`, which mixes
  Atlas, PPR, and ARE status.

One retained historical ARE document cites a PPR artifact for the P001 origin.
That citation is not an active dependency and does not import the artifact.
