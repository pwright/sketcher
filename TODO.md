# TODO

## Extend YAML Schema for Frontend URL

**Context**: Currently, the demo mode hardcodes `frontend_url = "http://localhost:8080/"` in `sketcher/demo.py:213` and prints it to the user.

**Task**: Extend the skewer YAML schema to support an optional `frontend-url` field that can be specified per-example/demo.

**Benefits**:
- Allow different examples to specify different frontend URLs
- Make the frontend URL configurable rather than hardcoded
- Support examples where the frontend is not at localhost:8080

**Implementation Notes**:
- Add optional `frontend-url` field to YAML schema
- Update `demo.py` to read from schema instead of hardcoding
- Update example YAML files as needed

**Related Files**:
- `sketcher/demo.py:238-240` (commented out print statement)
- `sketcher/demo.py:213` (hardcoded URL)
- Example YAML files in `examples/`
