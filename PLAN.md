# Product development plan

Each round completes one feature or repair. Future items are planned, not implemented claims.

## Current round

project-skeleton

## Roadmap

### project-skeleton — Project skeleton with FastAPI backend and React frontend

Status: done

Acceptance:
- FastAPI app runs on port 8000
- React app runs on port 3000
- Health endpoint returns 200 OK
- Frontend can call backend API

Implementation: `backend/main.py`, `backend/requirements.txt`, `frontend/package.json`, `frontend/src/App.tsx`, `frontend/src/main.tsx`

Tests: `backend/tests/test_health.py`

### vtable-display — VTable function call display in decompiler

Status: planned

Acceptance:
- Decompiler shows resolved vtable function names for indirect calls
- User can navigate from call site to vtable target

### switch-recognition — Switch statement recognition for jump tables

Status: planned

Acceptance:
- Decompiler recognizes jump table patterns
- Produces switch/case output instead of if/else chains

### call-return-analysis — PUSH+JMP call/return analysis

Status: planned

Acceptance:
- Recognizes PUSH return address + JMP as CALL
- Decompiler continues after call instead of returning

