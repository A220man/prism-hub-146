# Changelog

## 1.7.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.7.0 — switch-recognition feature

## 1.7.0 — switch-recognition feature

### Added
- **Switch statement recognition** for jump tables:
  - Backend: `POST /api/switch/analyze` recognizes jump table patterns and produces switch/case decompiled output
  - Pattern recognition fallback when database entry is not available
  - Recognizes consecutive case values, zero-based switches, and jump table structures
  - Frontend: SwitchAnalyzer component to be added in future round

### Changed
- backend/main.py: Added `recognize_switch_pattern()` and `generate_recognized_cases()` functions
- Tests: Both database lookup and no-database fallback test cases pass

### Test Results
- All 7 backend tests passing (2 switch + 3 vtable + 2 health + version)


Partial code published for continued development. Known issues: STATUS.md.

## 1.5.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.4.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.3.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.2.0 — 2026-11-08

### Completed
- **VTable Display** feature fully implemented and tested:
  - Backend: `POST /api/vtable/analyze` resolves vtable entries to function names with signatures
  - Frontend: Interactive VTableAnalyzer component with call site navigation and copy-to-clipboard
  - Cross-references: Shows call sites for each resolved vtable function
  - All 5 backend tests passing (2 health + 3 vtable)

### Added
- "Load Known Functions" button in VTableAnalyzer to fetch function database
- Clickable known functions list to auto-populate vtable entries
- Copy-to-clipboard button for call site addresses in results table

### Changed
- Frontend TypeScript compilation now passes with strict mode
- Updated README with completed feature documentation

## 1.1.0 — work-in-progress checkpoint (2026-11-05)

### Fixed
- Version mismatch: backend now reports 1.1.0 matching VERSION file

### Added
- "Load Known Functions" button in VTableAnalyzer to fetch function database
- Clickable known functions list to auto-populate vtable entries
- Copy-to-clipboard button for call site addresses in results table

### Changed
- Frontend TypeScript compilation now passes with strict mode

## 1.0.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

All notable changes to this project will be documented in this file.

## [0.1.0] - 2026-10-26

### Added
- FastAPI backend with health and version endpoints
- React + TypeScript frontend with Vite
- CORS configuration for frontend-backend communication
- Health check endpoint test
- Basic project structure and documentation

## [0.2.0] - 2026-11-01

### Added
- VTable function call analysis endpoint (`POST /api/vtable/analyze`)
- Known functions listing endpoint (`GET /api/vtable/functions`)
- VTableAnalyzer React component for interactive vtable analysis
- Cross-reference call site display for resolved vtable functions
- Backend tests for vtable endpoints (3 test cases)

### Planned
- Switch statement recognition for jump tables
- PUSH+JMP call/return analysis
- M68000 lineA/lineF opcode implementation
- Cross-segment string display in decompiler
- Batch decompilation performance improvements
