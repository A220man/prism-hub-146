from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="Prism Hub API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class VTableEntry(BaseModel):
    index: int
    address: str
    function_name: Optional[str] = None
    signature: Optional[str] = None


class VTableAnalyzeRequest(BaseModel):
    class_name: str
    vtable_address: str
    entries: List[VTableEntry]


class VTableAnalyzeResponse(BaseModel):
    class_name: str
    vtable_address: str
    resolved_entries: List[VTableEntry]
    call_sites: List[dict]


# Mock function database - in real implementation this would query the binary
FUNCTION_DB = {
    "0x401000": {"name": "BaseClass::virtualFunc1", "signature": "virtualFunc1(int) -> void"},
    "0x401050": {"name": "BaseClass::virtualFunc2", "signature": "virtualFunc2(float) -> int"},
    "0x4010a0": {"name": "BaseClass::virtualFunc3", "signature": "virtualFunc3() -> bool"},
    "0x402000": {"name": "DerivedClass::virtualFunc1", "signature": "virtualFunc1(int) -> void"},
    "0x402050": {"name": "DerivedClass::virtualFunc2", "signature": "virtualFunc2(float) -> int"},
    "0x4020a0": {"name": "DerivedClass::virtualFunc3", "signature": "virtualFunc3() -> bool"},
    "0x4020f0": {"name": "DerivedClass::virtualFunc4", "signature": "virtualFunc4(double) -> void"},
}

# Mock call sites - in real implementation this would be found via cross-references
CALL_SITES_DB = {
    "0x401000": [{"address": "0x405010", "function": "caller1", "instruction": "call rax"}],
    "0x401050": [{"address": "0x405020", "function": "caller2", "instruction": "call rdx"}],
    "0x402000": [{"address": "0x406010", "function": "derivedCaller", "instruction": "call rax"}],
}


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "prism-hub"}


@app.get("/api/version")
async def version():
    return {"version": "0.1.0", "name": "prism-hub"}


@app.post("/api/vtable/analyze", response_model=VTableAnalyzeResponse)
async def analyze_vtable(request: VTableAnalyzeRequest):
    """
    Analyze a vtable and resolve function names for indirect calls.
    Returns resolved entries and call sites for navigation.
    """
    resolved_entries = []
    all_call_sites = []
    
    for entry in request.entries:
        func_info = FUNCTION_DB.get(entry.address)
        if func_info:
            resolved_entry = VTableEntry(
                index=entry.index,
                address=entry.address,
                function_name=func_info["name"],
                signature=func_info["signature"]
            )
            # Add call sites for this function
            call_sites = CALL_SITES_DB.get(entry.address, [])
            for cs in call_sites:
                cs["vtable_index"] = entry.index
                cs["vtable_address"] = request.vtable_address
            all_call_sites.extend(call_sites)
        else:
            resolved_entry = VTableEntry(
                index=entry.index,
                address=entry.address,
                function_name=f"sub_{entry.address[2:]}",  # Generic name
                signature=None
            )
        resolved_entries.append(resolved_entry)
    
    return VTableAnalyzeResponse(
        class_name=request.class_name,
    vtable_address=request.vtable_address,
    resolved_entries=resolved_entries,
    call_sites=all_call_sites
    )


@app.get("/api/vtable/functions")
async def list_known_functions():
    """List all known functions in the database for vtable resolution."""
    return [
        {"address": addr, "name": info["name"], "signature": info["signature"]}
        for addr, info in FUNCTION_DB.items()
    ]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
