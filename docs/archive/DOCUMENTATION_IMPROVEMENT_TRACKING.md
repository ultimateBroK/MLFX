# Documentation Improvement Tracking

This document tracks the documentation restructuring work defined in `docs/DOCS_RESTRUCTURE_PLAN.md` and records what has already been completed, what still needs attention, and what should be verified before the restructuring is considered finished.

---

## 1. Scope

This tracking file covers:

- Documentation tree restructuring
- Bilingual symmetry between English and Vietnamese docs
- Quickstart deduplication
- Relocation of archive/meta materials
- Creation of missing reference documents
- Link and navigation cleanup
- Final acceptance checks

This file is intentionally stored under `docs/archive/` because it is a **tracking artifact**, not a primary user-facing document.

---

## 2. Current Restructure Status

### Overall status

**Completed**

The new documentation structure has now been implemented at the folder level and at the main documentation-entrypoint level. The docs tree is split by language and document category, the main files have been moved into their target locations, the canonical Quickstart files have been added, missing Vietnamese reference docs have been created, backend comparison docs have been added, the old `storings/` folder has been removed, and the final cleanup pass has been completed.

The remaining work, if any, is no longer part of the main restructuring effort. Any future adjustments should be treated as normal documentation maintenance rather than restructure follow-up.

### High-level completion summary

| Area | Status | Notes |
|---|---|---|
| Create target folder structure | ✅ Done | `en/`, `vi/`, `archive/` and category folders created |
| Move Vietnamese root docs into `docs/vi/` | ✅ Done | Main Vietnamese docs moved out of `docs/` root |
| Reorganize English docs by category | ✅ Done | English docs moved into grouped folders |
| Archive tracking material | ✅ Done | This file moved under `docs/archive/` |
| Create Vietnamese `README.md` | ✅ Done | Added as the Vietnamese docs hub |
| Create `QUICKSTART.md` for both languages | ✅ Done | Canonical Quickstart docs added under `getting-started/` |
| Add Vietnamese `CONFIG_REFERENCE.md` | ✅ Done | Added under `docs/vi/reference/` |
| Add Vietnamese `API_REFERENCE.md` | ✅ Done | Added under `docs/vi/reference/` |
| Add backend comparison docs | ✅ Done | Added in both English and Vietnamese architecture sections |
| Refresh navigation and internal links | ✅ Done | Main hubs updated and moved-doc links cleaned up |
| Remove outdated references to `TODO.md` | ✅ Done | Main navigation and repo-root references cleaned up |
| Validate all Markdown links | ✅ Done | Final sweep completed for restructure-related links |
| Remove legacy `storings/` folder | ✅ Done | Old folder deleted |

---

## 3. Current Documentation Structure

### Current tree snapshot

```/dev/null/docs-current-structure.txt#L1-40
docs/
├── README.md
├── DOCS_RESTRUCTURE_PLAN.md
├── archive/
│   ├── DOCUMENTATION_IMPROVEMENT_TRACKING.md
│   └── legacy/
├── en/
│   ├── README.md
│   ├── architecture/
│   │   ├── ARCHITECTURE.md
│   │   └── BACKEND_COMPARISON.md
│   ├── getting-started/
│   │   ├── NOOB_GUIDE.md
│   │   └── QUICKSTART.md
│   ├── guides/
│   │   ├── EVALUATION_GUIDE.md
│   │   ├── TROUBLESHOOTING.md
│   │   └── USAGE_GUIDE.md
│   ├── meta/
│   │   └── ROADMAP.md
│   └── reference/
│       ├── API_REFERENCE.md
│       ├── CONFIG_REFERENCE.md
│       ├── FEATURE_REFERENCE.md
│       └── GLOSSARY.md
└── vi/
    ├── README.md
    ├── architecture/
    │   ├── ARCHITECTURE.md
    │   └── BACKEND_COMPARISON.md
    ├── getting-started/
    │   ├── NOOB_GUIDE.md
    │   └── QUICKSTART.md
    ├── guides/
    │   ├── EVALUATION_GUIDE.md
    │   ├── TROUBLESHOOTING.md
    │   └── USAGE_GUIDE.md
    ├── meta/
    │   └── ROADMAP.md
    └── reference/
        ├── API_REFERENCE.md
        ├── CONFIG_REFERENCE.md
        ├── FEATURE_REFERENCE.md
        └── GLOSSARY.md
```

### Structural observations

- The language split is now in place.
- Category-based grouping is also in place:
  - `getting-started/`
  - `guides/`
  - `reference/`
  - `architecture/`
  - `meta/`
  - `archive/`
- `docs/storings/` has been removed.
- `docs/vi/` now has the core files needed for bilingual symmetry at the structure level.
- `docs/README.md`, `docs/en/README.md`, and `docs/vi/README.md` have been refreshed to reflect the new structure.
- The top-level structure and major moved-document navigation have been cleaned up and normalized.

---

## 4. Completed Work

## 4.1 Folder restructuring

Completed:

- Created `docs/archive/`
- Created `docs/archive/legacy/`
- Created `docs/en/getting-started/`
- Created `docs/en/guides/`
- Created `docs/en/reference/`
- Created `docs/en/architecture/`
- Created `docs/en/meta/`
- Created `docs/vi/getting-started/`
- Created `docs/vi/guides/`
- Created `docs/vi/reference/`
- Created `docs/vi/architecture/`
- Created `docs/vi/meta/`

---

## 4.2 Vietnamese document moves

Completed moves:

| Old path | New path |
|---|---|
| `docs/NOOB_GUIDE.md` | `docs/vi/getting-started/NOOB_GUIDE.md` |
| `docs/USAGE_GUIDE.md` | `docs/vi/guides/USAGE_GUIDE.md` |
| `docs/EVALUATION_GUIDE.md` | `docs/vi/guides/EVALUATION_GUIDE.md` |
| `docs/TROUBLESHOOTING.md` | `docs/vi/guides/TROUBLESHOOTING.md` |
| `docs/FEATURE_REFERENCE.md` | `docs/vi/reference/FEATURE_REFERENCE.md` |
| `docs/GLOSSARY.md` | `docs/vi/reference/GLOSSARY.md` |
| `docs/ARCHITECTURE.md` | `docs/vi/architecture/ARCHITECTURE.md` |

Result:
- `docs/` root no longer acts as the Vietnamese docs container for these primary files.

---

## 4.3 English document moves

Completed moves:

| Old path | New path |
|---|---|
| `docs/en/NOOB_GUIDE.md` | `docs/en/getting-started/NOOB_GUIDE.md` |
| `docs/en/USAGE_GUIDE.md` | `docs/en/guides/USAGE_GUIDE.md` |
| `docs/en/EVALUATION_GUIDE.md` | `docs/en/guides/EVALUATION_GUIDE.md` |
| `docs/en/TROUBLESHOOTING.md` | `docs/en/guides/TROUBLESHOOTING.md` |
| `docs/en/FEATURE_REFERENCE.md` | `docs/en/reference/FEATURE_REFERENCE.md` |
| `docs/en/GLOSSARY.md` | `docs/en/reference/GLOSSARY.md` |
| `docs/en/CONFIG_REFERENCE.md` | `docs/en/reference/CONFIG_REFERENCE.md` |
| `docs/en/API_REFERENCE.md` | `docs/en/reference/API_REFERENCE.md` |
| `docs/en/ARCHITECTURE.md` | `docs/en/architecture/ARCHITECTURE.md` |
| `docs/en/ROADMAP.md` | `docs/en/meta/ROADMAP.md` |

Result:
- English docs are now grouped by document type instead of a flat folder layout.

---

## 4.4 Archive relocation

Completed:

| Old path | New path |
|---|---|
| `docs/DOCUMENTATION_IMPROVEMENT_TRACKING.md` | `docs/archive/DOCUMENTATION_IMPROVEMENT_TRACKING.md` |

Result:
- Tracking material is no longer mixed with user-facing documentation.

---

## 5. Final Cleanup Results

## 5.1 Canonical entrypoints

### `docs/vi/README.md`
Status: **done**

Completed:
- Added as the Vietnamese docs hub
- Links to the new grouped structure
- Mirrors the role of the English docs hub

### `docs/en/README.md`
Status: **updated**

Completed:
- Refreshed to reflect grouped folders
- Points to `getting-started/`, `guides/`, `reference/`, `architecture/`, and `meta/`
- No longer acts like a flat-folder index

Final result:
- Linked targets in the main navigation and updated guides were reviewed during the cleanup pass

### `docs/README.md`
Status: **updated**

Completed:
- Converted into a bilingual navigation hub
- Updated to reflect the new categorized docs tree
- Now points readers into the correct language branches

Final result:
- The bilingual hub structure now reflects the implemented docs tree

---

## 5.2 Canonical quickstart docs

### `docs/en/getting-started/QUICKSTART.md`
Status: **done**

### `docs/vi/getting-started/QUICKSTART.md`
Status: **done**

Completed:
- Both canonical Quickstart docs were added
- The Quickstart path is now separated from the broader guide/reference materials

Final result:
- Hub docs point to the canonical Quickstart files
- The main duplicated Quickstart sections targeted during the restructure were trimmed or redirected

---

## 5.3 Vietnamese reference parity

### `docs/vi/reference/CONFIG_REFERENCE.md`
Status: **done**

### `docs/vi/reference/API_REFERENCE.md`
Status: **done**

Completed:
- Both Vietnamese reference files were added
- The Vietnamese reference tree now mirrors the English reference tree at the major-file level

---

## 5.4 Backend comparison docs

### `docs/en/architecture/BACKEND_COMPARISON.md`
Status: **done**

### `docs/vi/architecture/BACKEND_COMPARISON.md`
Status: **done**

Completed:
- Added backend comparison docs in both languages
- Documented backend selection guidance, trade-offs, and benchmarking strategy

---

## 5.5 Meta cleanup

### `docs/storings/`
Status: **done**

Completed:
- Removed the old folder
- `docs/archive/legacy/` remains the intended place for future legacy materials if needed

### `docs/vi/meta/`
Status: **done**

Completed:
- Added `ROADMAP.md`
- Vietnamese meta/docs-planning branch now exists

---

## 5.6 Link cleanup after moves

Status: **done**

Completed during the final cleanup pass:
- Main `README` files were updated
- Moved Vietnamese docs were updated to use new relative paths
- English guide links were normalized
- Repo-root references into `docs/` were refreshed
- Stale references to the old flat structure were cleaned up
- Stale `TODO.md` references related to the restructure were removed

Result:
- Link cleanup for the restructuring scope is complete

---

## 6. Redundancy Cleanup Status

## 6.1 Quickstart duplication

### Before restructure
Quickstart content was spread across:
- `README`
- `NOOB_GUIDE`
- `USAGE_GUIDE`

### Current status
**Addressed**

What has already changed:
- Canonical `QUICKSTART.md` now exists in both languages
- Vietnamese `NOOB_GUIDE.md` now points readers to `QUICKSTART.md` instead of embedding the full Quickstart flow
- Vietnamese `USAGE_GUIDE.md` now frames itself as an operational CLI manual and points readers to `QUICKSTART.md`
- English `NOOB_GUIDE.md` now points readers to `QUICKSTART.md`
- English `USAGE_GUIDE.md` now more clearly frames itself as the operational CLI manual and points readers to `QUICKSTART.md`

Result:
- The Quickstart hierarchy is now in place across both language trees

---

## 6.2 Beginner vs operational split

### Target intent
- `NOOB_GUIDE.md` = why the workflow exists and what each stage means
- `USAGE_GUIDE.md` = how to run commands and what flags/artifacts matter

### Current status
**Normalized for restructure scope**

Observations:
- `NOOB_GUIDE.md` is now more clearly conceptual on both language sides
- `USAGE_GUIDE.md` now more clearly identifies itself as the CLI manual on both language sides

Result:
- The beginner-vs-operational split is now aligned with the restructure plan
- Command-by-command reference remains intact

---

## 7. Bilingual Symmetry Status

## 7.1 Current comparison

| Category | English | Vietnamese | Status |
|---|---|---|---|
| README | `docs/en/README.md` | `docs/vi/README.md` | ✅ Present |
| Getting started | `NOOB_GUIDE.md` | `NOOB_GUIDE.md` | ✅ Present |
| Quickstart | `QUICKSTART.md` | `QUICKSTART.md` | ✅ Present |
| Usage guide | `USAGE_GUIDE.md` | `USAGE_GUIDE.md` | ✅ Present |
| Evaluation guide | `EVALUATION_GUIDE.md` | `EVALUATION_GUIDE.md` | ✅ Present |
| Troubleshooting | `TROUBLESHOOTING.md` | `TROUBLESHOOTING.md` | ✅ Present |
| Feature reference | `FEATURE_REFERENCE.md` | `FEATURE_REFERENCE.md` | ✅ Present |
| Config reference | `CONFIG_REFERENCE.md` | `CONFIG_REFERENCE.md` | ✅ Present |
| API reference | `API_REFERENCE.md` | `API_REFERENCE.md` | ✅ Present |
| Glossary | `GLOSSARY.md` | `GLOSSARY.md` | ✅ Present |
| Architecture | `ARCHITECTURE.md` | `ARCHITECTURE.md` | ✅ Present |
| Backend comparison | `BACKEND_COMPARISON.md` | `BACKEND_COMPARISON.md` | ✅ Present |
| Roadmap/meta | `ROADMAP.md` | `ROADMAP.md` | ✅ Present |

### Conclusion
The bilingual structure is now complete at the major-document level. The remaining work is primarily about cleanup quality, navigation validation, and consistency polishing rather than missing core files.

---

## 8. Recommended Next Actions

## Priority 1 — completed in final cleanup

Completed:
1. Verified and cleaned key relative links after the moves
2. Reviewed repo-root references into `docs/`
3. Removed stale old-structure references that were part of the restructure scope

---

## Priority 2 — completed in final cleanup

Completed:
1. Trimmed remaining duplicated quickstart sections targeted by the restructure
2. Aligned entrypoint docs to point to `QUICKSTART.md`
3. Normalized the same pattern across the main English and Vietnamese guides

---

## Priority 3 — completed at restructure scope

Completed:
1. Restored document parity at the major-file level across both language trees
2. Added the missing Vietnamese reference files
3. Added backend comparison docs in both languages

---

## Priority 4 — completed at restructure scope

Completed:
1. Kept tracking and archive-oriented material under `archive/`
2. Removed the legacy `storings/` folder
3. Added the Vietnamese meta roadmap branch

---

## 9. Acceptance Checklist

## Structure
- [x] language-specific directories exist
- [x] category-based subdirectories exist
- [x] major Vietnamese docs moved out of `docs/` root
- [x] major English docs grouped into categorized folders
- [x] tracking document moved into `archive/`
- [x] `storings/` removed or retired cleanly

## Navigation
- [x] `docs/README.md` matches new tree at a high level
- [x] `docs/en/README.md` matches new tree at a high level
- [x] `docs/vi/README.md` exists
- [x] all relative links work after moves for the restructure scope
- [x] no stale `TODO.md` references remain for the restructure scope

## Content model
- [x] canonical `QUICKSTART.md` exists in both languages
- [x] `NOOB_GUIDE.md` is conceptual, not command-heavy for the restructure scope
- [x] `USAGE_GUIDE.md` is operational, not duplicating quickstart for the restructure scope
- [x] reference docs are separated from guides
- [x] meta/tracking docs are separated from user docs

## Bilingual parity
- [x] `CONFIG_REFERENCE.md` exists in both languages
- [x] `API_REFERENCE.md` exists in both languages
- [x] `BACKEND_COMPARISON.md` exists in both languages
- [x] `README.md` exists for both language branches or an explicit policy is documented

---

## 10. Post-restructure Maintenance Risks

### Consistency drift
Even though the major bilingual files now exist, the two language trees may still drift in wording, scope, or navigation quality over time.

### Future link regressions
The restructure-related links have been cleaned up, but future document moves or additions could reintroduce broken relative links if not reviewed carefully.

### Archive policy drift
Now that `storings/` is gone, future planning and legacy notes should consistently go to either `meta/` or `archive/` to avoid recreating ambiguity.

---

## 11. Suggested Close-Out Criteria

The restructuring is now considered complete for the planned scope because all of the following are true:

1. The new tree is reflected in the README/index files
2. The moved docs and main navigation were cleaned up for the restructure scope
3. Stale old-structure references targeted by the cleanup were removed
4. The bilingual trees are complete enough for normal maintenance
5. Legacy/archive folders now have clear ownership
6. The acceptance checklist above is checked off for the restructure scope

---

## 12. Final Status Summary

### What is already good
- The structural refactor has been executed successfully
- The language split is now real
- The category grouping is much clearer
- Archive tracking is separated from user docs
- Bilingual parity exists at the major-file level
- Canonical quickstart files are in place

### What matters next
- Keep future doc changes aligned across both language trees
- Preserve the beginner / quickstart / usage separation
- Review links whenever files are moved again
- Keep archive and meta material separated from user-facing docs

---

*Last updated: after executing the main restructure plan, follow-up content additions, and final cleanup pass*
