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


# Switch pattern recognition - identifies jump table patterns from case data
def recognize_switch_pattern(switch_variable, cases):
    """
    Recognize jump table patterns from switch case data.

    Analyzes the structure of cases to identify common switch statement
    implementations in assembly, particularly the pattern where a variable
    is compared against array elements and used as an index into a jump table.

    Returns a dict with recognized pattern info or None if no pattern matches.
    """
    if not cases or len(cases) < 2:
        return None

    # Sort cases by case_value for analysis
    sorted_cases = sorted(cases, key=lambda c: c.case_value)

    # Check for consecutive integer case values (typical switch pattern)
    case_values = [c.case_value for c in sorted_cases]
    if len(case_values) < 2:
        return None

    # Check if case values form a consecutive range
    is_consecutive = all(
        case_values[i] + 1 == case_values[i + 1]
        for i in range(len(case_values) - 1)
    )

    if not is_consecutive:
        # Not a typical consecutive-switch pattern, but might still be a jump table
        # Check if there are multiple distinct targets
        target_addresses = set(c.target_address for c in sorted_cases)
        if len(target_addresses) >= 2:
            # Has multiple targets - could be a jump table with non-consecutive cases
            return {
                'pattern': 'jump_table',
                'variable': switch_variable,
                'case_count': len(cases),
                'case_values': case_values,
                'targets': list(target_addresses),
            }

    # Consecutive case values - this is a classic switch statement pattern
    first_value = case_values[0]
    last_value = case_values[-1]
    expected_range = list(range(first_value, last_value + 1))

    if case_values == expected_range:
        # Perfect consecutive range starting from first_value
        return {
            'pattern': 'switch_statement',
            'variable': switch_variable,
            'case_count': len(cases),
            'range': (first_value, last_value),
            'case_values': case_values,
        }

    # Check for common patterns: starting from 0, 1, or other defaults
    if first_value == 0 and is_consecutive:
        return {
            'pattern': 'switch_zero_based',
            'variable': switch_variable,
            'case_count': len(cases),
            'range': (0, last_value),
        }

    if is_consecutive:
        # Any consecutive range is recognizable as a switch pattern
        return {
            'pattern': 'consecutive_switch',
            'variable': switch_variable,
            'case_count': len(cases),
            'range': (first_value, last_value),
        }

    return None


def generate_recognized_cases(switch_variable, cases, default_case=None, db_entry=None):
    """
    Generate recognized cases and decompiled output from case data,
    using pattern recognition as fallback when DB doesn't have the entry.
    """
    # Try pattern recognition first
    pattern = recognize_switch_pattern(switch_variable, cases)

    recognized_cases_list = []
    output_default_case = default_case

    if pattern:
        # Use pattern-based recognition
        case_count = pattern['case_count']
        case_values = pattern.get('case_values', [c.case_value for c in cases])

        for i, case in enumerate(cases[:case_count]):
            case_value = case.case_value if i < len(case_values) else case_values[-1] if case_values else 0
            target_address = case.target_address
            target_function = case.target_function

            recognized_cases_list.append({
                'case_value': case_value,
                'target_address': target_address,
                'target_function': target_function,
            })

        # Handle default case based on pattern
        if default_case is not None:
            output_default_case = default_case
        elif pattern.get('pattern') == 'switch_statement':
            # For a standard switch, add a default case if not already present
            # Check if any case has a default marker
            has_default = any(case.target_function and 'default' in str(case.target_function).lower() for case in cases)
            if not has_default:
                output_default_case = 'default_handler'

    else:
        # No pattern recognized, use cases as-is
        for case in cases:
            recognized_cases_list.append({
                'case_value': case.case_value,
                'target_address': case.target_address,
                'target_function': case.target_function,
            })

        # Use provided default_case or None
        output_default_case = default_case

    return recognized_cases_list, output_default_case


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
    Uses pattern recognition as fallback when database entry is not available.
    """
    # Check if we have this in our database
    db_entry = SWITCH_DB.get(request.function_address)

    # Try pattern recognition as fallback
    recognized_cases_list, default_case = generate_recognized_cases(
        request.switch_variable,
        request.cases,
        request.default_case,
        db_entry
    )

    # Convert to SwitchCase model instances
    switch_cases = []
    for case in recognized_cases_list:
        switch_cases.append(SwitchCase(
            case_value=case['case_value'],
            target_address=case['target_address'],
            target_function=case.get('target_function')
        ))

    # Generate decompiled switch output
    decompiled_lines = [f"switch ({request.switch_variable}) {{"]
    for case in switch_cases:
        func_name = case.target_function or f"sub_{case.target_address[2:]}"
        decompiled_lines.append(f"    case {case.case_value}:")
        decompiled_lines.append(f"        {func_name}();")
        decompiled_lines.append(f"        break;")
    if default_case:
        # Use requested default_case name
        default_func = default_case
        decompiled_lines.append(f"    default:")
        decompiled_lines.append(f"        {default_func}();")
        decompiled_lines.append(f"        break;")
    decompiled_lines.append("}")
    decompiled_output = "\n".join(decompiled_lines)

    return SwitchAnalyzeResponse(
        function_address=request.function_address,
        jump_table_address=request.jump_table_address,
        switch_variable=request.switch_variable,
        recognized_cases=switch_cases,
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
