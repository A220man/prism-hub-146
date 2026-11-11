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


# Switch recognition models
class SwitchCase(BaseModel):
    case_value: int
    target_address: str
    target_function: Optional[str] = None


class SwitchAnalyzeRequest(BaseModel):
    function_address: str
    jump_table_address: str
    switch_variable: str
    cases: List[SwitchCase]
    default_case: Optional[str] = None


class SwitchAnalyzeResponse(BaseModel):
    function_address: str
    jump_table_address: str
    switch_variable: str
    recognized_cases: List[SwitchCase]
    default_case: Optional[str] = None
    decompiled_output: str


# Mock switch database - in real implementation this would analyze the binary
SWITCH_DB = {
    "0x401000": {
        "jump_table_address": "0x403000",
        "switch_variable": "eax",
        "cases": [
            {"case_value": 0, "target_address": "0x401100", "target_function": "case_zero_handler"},
            {"case_value": 1, "target_address": "0x401150", "target_function": "case_one_handler"},
            {"case_value": 2, "target_address": "0x4011a0", "target_function": "case_two_handler"},
            {"case_value": 3, "target_address": "0x4011f0", "target_function": "case_three_handler"},
        ],
        "default_case": "0x401250",
    },
    "0x402000": {
        "jump_table_address": "0x404000",
        "switch_variable": "ecx",
        "cases": [
            {"case_value": 10, "target_address": "0x402100", "target_function": "case_ten_handler"},
            {"case_value": 20, "target_address": "0x402150", "target_function": "case_twenty_handler"},
            {"case_value": 30, "target_address": "0x4021a0", "target_function": "case_thirty_handler"},
        ],
        "default_case": "0x402200",
    },
}


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "prism-hub"}


@app.get("/api/version")
async def version():
    return {"version": "1.2.0", "name": "prism-hub"}


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


@app.post("/api/switch/analyze", response_model=SwitchAnalyzeResponse)
async def analyze_switch(request: SwitchAnalyzeRequest):
    """
    Analyze a jump table pattern and produce switch/case decompiled output.
    Recognizes common switch statement implementations in assembly.
    """
    # Check if we have this in our database
    db_entry = SWITCH_DB.get(request.function_address)
    
    recognized_cases = []
    default_case = request.default_case
    
    if db_entry:
        # Use database entry
        for case in db_entry["cases"]:
            recognized_cases.append(SwitchCase(**case))
        default_case = db_entry.get("default_case", request.default_case)
    else:
        # Use provided cases
        recognized_cases = request.cases
    
    # Generate decompiled switch output
    decompiled_lines = [f"switch ({request.switch_variable}) {{"]
    for case in recognized_cases:
        func_name = case.target_function or f"sub_{case.target_address[2:]}"
        decompiled_lines.append(f"    case {case.case_value}:")
        decompiled_lines.append(f"        {func_name}();")
        decompiled_lines.append(f"        break;")
    if default_case:
        default_func = "default_handler"
        if db_entry and default_case == db_entry.get("default_case"):
            default_func = "default_handler"
        decompiled_lines.append(f"    default:")
        decompiled_lines.append(f"        {default_func}();")
        decompiled_lines.append(f"        break;")
    decompiled_lines.append("}")
    decompiled_output = "\n".join(decompiled_lines)
    
    return SwitchAnalyzeResponse(
        function_address=request.function_address,
        jump_table_address=request.jump_table_address,
        switch_variable=request.switch_variable,
        recognized_cases=recognized_cases,
        default_case=default_case,
        decompiled_output=decompiled_output
    )


@app.get("/api/switch/functions")
async def list_switch_functions():
    """List all known functions with switch statements."""
    return [
        {"address": addr, "jump_table": info["jump_table_address"], "variable": info["switch_variable"]}
        for addr, info in SWITCH_DB.items()
    ]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
