# Prism Hub

> Work in progress. This checkpoint may be incomplete or fail tests. See PLAN.md and STATUS.md before use.


AI/ML Developer Tools Platform - inspired by Ghidra's reverse engineering capabilities.

## Architecture

- **Backend**: FastAPI (Python) on port 8000
- **Frontend**: React + TypeScript + Vite on port 3000

## Quick Start

### Backend

```bash
cd backend
pip install -r requirements.txt
python main.py
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## API Endpoints

- `GET /health` - Health check
- `GET /api/version` - Version information

## Features (Planned)

Based on Ghidra issue analysis:
1. **VTable Display** - Show resolved vtable function names in decompiler
2. **Switch Recognition** - Recognize jump table patterns as switch statements
3. **Call/Return Analysis** - Handle PUSH+JMP as proper CALL with return continuation
4. **M68000 LineA/LineF** - Implement Motorola 68000 lineA/lineF opcodes
5. **String Display** - Display strings in decompiler across memory segments
6. **Batch Decompilation Performance** - Improve concurrent decompilation scaling

## License

Apache-2.0

Maintainer: Ryan Vo <ryandtvo@gmail.com>
