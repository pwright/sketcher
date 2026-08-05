# Schema Modeling Analysis for skewer.yaml

This document analyzes different approaches for modeling the `skewer.yaml` schema in both Python and Go implementations of Sketcher.

## Table of Contents

- [Python Implementation](#python-implementation)
  - [Current Approach (Recommended)](#current-approach-recommended)
  - [Alternative: Pydantic](#alternative-1-pydantic-strict-validation)
  - [Alternative: Dataclasses](#alternative-2-python-310-dataclasses)
  - [Alternative: attrs](#alternative-3-attrs-middle-ground)
  - [Python Recommendation](#python-recommendation)
- [Go Implementation](#go-implementation)
  - [Current Approach (Recommended)](#current-approach-structs-with-manual-parsing)
  - [Alternative: Struct Tags with Validation](#alternative-1-struct-tags-with-validation-library)
  - [Alternative: Code Generation](#alternative-2-code-generation-from-schema)
  - [Alternative: Interface-based Approach](#alternative-3-interface-based-approach)
  - [Go Recommendation](#go-recommendation)
- [Cross-Language Considerations](#cross-language-considerations)

---

## Python Implementation

### Current Approach (Recommended)

**File:** `sketcher/model.py`

The current implementation uses a custom property descriptor pattern:

```python
def object_property(name: str, default: Any = None):
    """Property descriptor with @default@ text substitution."""
    def get(obj):
        value = obj.data.get(name, default)
        if isinstance(value, str):
            value = value.replace("@default@", str(default or "").strip())
            value = value.strip()
        return value
    return property(get)

class Model:
    title = object_property("title")
    subtitle = object_property("subtitle")
    workflow = object_property("workflow", "main.yaml")
    overview = object_property("overview")
    prerequisites = object_property("prerequisites", _standard_text.get("prerequisites"))
    # ...
```

**Pros:**
- ✅ Zero external dependencies (PyYAML only)
- ✅ Lazy property access with deferred validation via `.check()`
- ✅ Built-in `@default@` text substitution
- ✅ Works perfectly with YAML dict access patterns
- ✅ Simple to understand and debug
- ✅ Matches project's "zero dependencies beyond PyYAML" philosophy
- ✅ Proven in production (63 passing tests, 63% of real Skupper examples)

**Cons:**
- ⚠️ No IDE autocomplete for property names
- ⚠️ Validation happens at `.check()` time, not parse time
- ⚠️ Type hints less explicit than modern approaches

**When to use:**
- ✅ Configuration file parsing with custom text substitution
- ✅ Projects with minimal dependencies requirement
- ✅ Lazy validation is acceptable
- ✅ YAML-to-object mapping is primary use case

---

### Alternative 1: Pydantic (Strict Validation)

If you wanted stricter validation and auto-documentation:

```python
from pydantic import BaseModel, Field
from typing import Optional, Dict, List

class SiteSchema(BaseModel):
    title: Optional[str] = None
    platform: str = Field(..., pattern="^(kubernetes|podman|docker|linux)$")
    namespace: Optional[str] = None
    env: Dict[str, str] = Field(default_factory=dict)
    
    model_config = {
        "extra": "forbid"  # Reject unknown fields
    }

class CommandSchema(BaseModel):
    run: Optional[str] = None
    apply: Optional[str] = Field(None, pattern="^(readme|test)$")
    output: Optional[str] = None
    expect_failure: bool = False
    await_resource: Optional[str] = None
    await_ingress: Optional[str] = None
    await_http_ok: Optional[List[str]] = None
    await_console_ok: Optional[bool] = None
    await_port: Optional[int] = None

class StepSchema(BaseModel):
    title: str
    numbered: bool = True
    name: Optional[str] = None
    preamble: Optional[str] = None
    commands: Dict[str, List[CommandSchema]] = Field(default_factory=dict)
    postamble: Optional[str] = None

class SkewerSchema(BaseModel):
    title: str
    subtitle: Optional[str] = None
    workflow: str = "main.yaml"
    overview: Optional[str] = None
    prerequisites: Optional[str] = None
    sites: Dict[str, SiteSchema]
    steps: List[StepSchema]
    summary: Optional[str] = None
    next_steps: Optional[str] = None
    
    model_config = {
        "extra": "forbid"
    }

# Usage:
model = SkewerSchema.model_validate(yaml_data)
```

**Pros:**
- ✅ Automatic validation on parse
- ✅ JSON Schema export (`model.model_json_schema()`)
- ✅ Excellent IDE autocomplete and type checking
- ✅ Self-documenting with Field descriptions
- ✅ Built-in validators (regex, range, custom functions)
- ✅ Serialization/deserialization for free

**Cons:**
- ❌ Adds `pydantic` dependency (~3MB, against zero-dependency goal)
- ❌ Overkill for simple YAML loading
- ❌ Harder to implement `@default@` substitution (would need custom validator)
- ❌ Performance overhead for validation (negligible for config files)

**When to use:**
- Need JSON Schema for external tools/documentation
- Want strict validation at parse time
- API development where validation errors must be detailed
- Okay with adding dependencies

---

### Alternative 2: Python 3.10+ Dataclasses

```python
from dataclasses import dataclass, field
from typing import Optional, Dict, List

@dataclass
class Site:
    platform: str
    title: Optional[str] = None
    namespace: Optional[str] = None
    env: Dict[str, str] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate after initialization."""
        if self.platform not in ("kubernetes", "podman", "docker", "linux"):
            raise ValueError(f"Invalid platform: {self.platform}")
        
        if self.platform == "kubernetes" and not self.namespace:
            raise ValueError("Kubernetes sites require namespace")

@dataclass
class Command:
    run: Optional[str] = None
    apply: Optional[str] = None
    output: Optional[str] = None
    expect_failure: bool = False
    await_resource: Optional[str] = None
    
    def __post_init__(self):
        if self.apply and self.apply not in ("readme", "test"):
            raise ValueError(f"Invalid apply value: {self.apply}")

@dataclass
class Step:
    title: str
    numbered: bool = True
    preamble: Optional[str] = None
    commands: Dict[str, List[Command]] = field(default_factory=dict)
    postamble: Optional[str] = None

@dataclass
class Model:
    title: str
    sites: Dict[str, Site]
    steps: List[Step]
    subtitle: Optional[str] = None
    workflow: str = "main.yaml"
    overview: Optional[str] = None
```

**Pros:**
- ✅ Built-in (Python 3.7+, enhanced in 3.10+)
- ✅ Type hints for IDE support
- ✅ No external dependencies
- ✅ Good for simple validation in `__post_init__`
- ✅ Standard Python idiom

**Cons:**
- ⚠️ Less validation than Pydantic
- ⚠️ Still need manual `@default@` substitution
- ⚠️ Requires converting YAML dict → dataclass instances (tedious)
- ⚠️ Mutable by default (use `@dataclass(frozen=True)` for immutability)

**When to use:**
- Need type hints but want zero dependencies
- Simple validation is sufficient
- Python 3.10+ only (can use older, but better in 3.10+)

---

### Alternative 3: attrs (Middle Ground)

```python
import attr
from attr import validators

@attr.s(auto_attribs=True)
class Site:
    platform: str = attr.ib(validator=validators.in_(["kubernetes", "podman", "docker", "linux"]))
    title: Optional[str] = None
    namespace: Optional[str] = None
    env: Dict[str, str] = attr.Factory(dict)
    
    @namespace.validator
    def check_namespace(self, attribute, value):
        if self.platform == "kubernetes" and not value:
            raise ValueError("Kubernetes sites require namespace")

@attr.s(auto_attribs=True)
class Command:
    run: Optional[str] = None
    apply: Optional[str] = attr.ib(
        default=None,
        validator=attr.validators.optional(validators.in_(["readme", "test"]))
    )
    expect_failure: bool = False
```

**Pros:**
- ✅ Lighter than Pydantic (~200KB)
- ✅ Built-in validators
- ✅ Good for Python 3.6+ compatibility
- ✅ More mature than dataclasses (existed before dataclasses)

**Cons:**
- ❌ Adds dependency (against project goal)
- ⚠️ Similar complexity to dataclasses
- ⚠️ Less popular than Pydantic or dataclasses

**When to use:**
- Need more validation than dataclasses
- Don't want Pydantic's weight
- Supporting Python < 3.7

---

### Python Recommendation

**Keep the current property descriptor approach.** It's:

- **Simple and effective** for configuration parsing
- **Dependency-free** (core project value)
- **Battle-tested** (63 passing tests, production-ready)
- **Perfectly adequate** for YAML → object mapping

**Optional enhancements (no dependencies):**

1. **Add type hints for better IDE support:**
```python
from typing import Any, Optional

def object_property(name: str, default: Any = None) -> property:
    """Property descriptor with @default@ text substitution."""
    def get(obj) -> Any:
        value = obj.data.get(name, default)
        if isinstance(value, str):
            value = value.replace("@default@", str(default or "").strip())
            value = value.strip()
        return value
    return property(get)
```

2. **Document schema separately (for humans, not validation):**
Create `sketcher/schema.yaml` as documentation:
```yaml
# Schema documentation for skewer.yaml (not enforced at runtime)
$schema: "http://json-schema.org/draft-07/schema#"
type: object
required: [title, sites, steps]
properties:
  title: {type: string, description: "Example title"}
  subtitle: {type: string, description: "Optional subtitle"}
  # ...
```

**Only adopt Pydantic/dataclasses if:**
- You need JSON Schema export for tooling integration
- You want validation errors at parse time (before `.check()`)
- You're comfortable adding dependencies

---

## Go Implementation

### Current Approach (Structs with Manual Parsing)

**File:** `internal/model/model.go`

The current Go implementation uses plain structs with manual parsing:

```go
// Model represents the top-level skewer.yaml structure
type Model struct {
    YAMLFile         string
    Data             map[string]interface{}
    Title            string
    Subtitle         string
    Workflow         string
    Overview         string
    Prerequisites    string
    Summary          string
    NextSteps        string
    AboutThisExample string
    Sites            []*Site
    Steps            []*Step
}

// Site represents a deployment site
type Site struct {
    Name      string
    Platform  string
    Namespace string
    Env       map[string]string
    Title     string
    Data      map[string]interface{}
}

// NewModel creates a new Model from a YAML file
func NewModel(yamlFile string, kubeconfigs []string) (*Model, error) {
    var data map[string]interface{}
    if err := utils.ReadYAML(yamlFile, &data); err != nil {
        return nil, err
    }

    model := &Model{
        YAMLFile: yamlFile,
        Data:     data,
    }

    if err := model.parse(); err != nil {
        return nil, err
    }

    return model, nil
}

func (m *Model) parse() error {
    m.Title = getString(m.Data, "title")
    m.Subtitle = getString(m.Data, "subtitle")
    m.Workflow = getStringWithDefault(m.Data, "workflow", "main.yaml")
    // ... manual parsing for all fields
}
```

**Pros:**
- ✅ Complete control over parsing logic
- ✅ No external dependencies (only `gopkg.in/yaml.v3`)
- ✅ Explicit error handling
- ✅ Easy to add custom `@default@` substitution
- ✅ Type-safe at compile time
- ✅ Single binary deployment with no runtime dependencies

**Cons:**
- ⚠️ Verbose boilerplate for field extraction
- ⚠️ Manual type assertions (`m.Data["title"].(string)`)
- ⚠️ Duplicate field definitions (struct + parsing code)
- ⚠️ Easy to forget fields when adding new ones

**When to use:**
- ✅ Need full control over parsing behavior
- ✅ Complex validation logic
- ✅ Custom text substitution (like `@default@`)
- ✅ Zero external dependencies requirement

---

### Alternative 1: Struct Tags with Validation Library

Using struct tags with `gopkg.in/yaml.v3` and `github.com/go-playground/validator/v10`:

```go
import (
    "gopkg.in/yaml.v3"
    "github.com/go-playground/validator/v10"
)

type Model struct {
    Title            string             `yaml:"title" validate:"required"`
    Subtitle         string             `yaml:"subtitle,omitempty"`
    Workflow         string             `yaml:"workflow,omitempty" default:"main.yaml"`
    Overview         string             `yaml:"overview,omitempty"`
    Prerequisites    string             `yaml:"prerequisites,omitempty"`
    Sites            map[string]*Site   `yaml:"sites" validate:"required,dive"`
    Steps            []*Step            `yaml:"steps" validate:"required,dive"`
    Summary          string             `yaml:"summary,omitempty"`
    NextSteps        string             `yaml:"next_steps,omitempty"`
    AboutThisExample string             `yaml:"about_this_example,omitempty"`
}

type Site struct {
    Title     string            `yaml:"title,omitempty"`
    Platform  string            `yaml:"platform" validate:"required,oneof=kubernetes podman docker linux"`
    Namespace string            `yaml:"namespace,omitempty" validate:"required_if=Platform kubernetes"`
    Env       map[string]string `yaml:"env,omitempty"`
}

type Command struct {
    Run            string   `yaml:"run,omitempty"`
    ExpectFailure  bool     `yaml:"expect_failure,omitempty"`
    Apply          string   `yaml:"apply,omitempty" validate:"omitempty,oneof=readme test"`
    Output         string   `yaml:"output,omitempty"`
    AwaitResource  string   `yaml:"await_resource,omitempty"`
    AwaitIngress   string   `yaml:"await_ingress,omitempty"`
    AwaitHTTPOK    []string `yaml:"await_http_ok,omitempty"`
    AwaitConsoleOK bool     `yaml:"await_console_ok,omitempty"`
    AwaitPort      int      `yaml:"await_port,omitempty"`
}

// Usage:
func NewModel(yamlFile string) (*Model, error) {
    data, err := os.ReadFile(yamlFile)
    if err != nil {
        return nil, err
    }
    
    var model Model
    if err := yaml.Unmarshal(data, &model); err != nil {
        return nil, err
    }
    
    validate := validator.New()
    if err := validate.Struct(&model); err != nil {
        return nil, err
    }
    
    return &model, nil
}
```

**Pros:**
- ✅ Declarative validation with struct tags
- ✅ Automatic YAML unmarshaling
- ✅ Less boilerplate than manual parsing
- ✅ Clear field mapping in one place
- ✅ Validation errors are detailed

**Cons:**
- ❌ Adds external dependency (`validator/v10`)
- ⚠️ Harder to implement `@default@` substitution
- ⚠️ Less control over parsing behavior
- ⚠️ Tag syntax can be cryptic

**When to use:**
- Standard YAML parsing without custom logic
- Want declarative validation
- Okay with external dependencies
- Don't need complex text substitution

---

### Alternative 2: Code Generation from Schema

Generate Go structs from a JSON Schema definition:

```bash
# Define schema in schema.json
# Use tools like:
# - github.com/atombender/go-jsonschema
# - github.com/a-h/generate

go-jsonschema --package model -o model_gen.go schema.json
```

**Example schema.json:**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["title", "sites", "steps"],
  "properties": {
    "title": {"type": "string"},
    "subtitle": {"type": "string"},
    "sites": {
      "type": "object",
      "additionalProperties": {
        "$ref": "#/definitions/Site"
      }
    }
  },
  "definitions": {
    "Site": {
      "type": "object",
      "required": ["platform"],
      "properties": {
        "platform": {
          "type": "string",
          "enum": ["kubernetes", "podman", "docker", "linux"]
        }
      }
    }
  }
}
```

**Pros:**
- ✅ Single source of truth (JSON Schema)
- ✅ Auto-generate Go structs + validation
- ✅ Schema can be shared with other tools
- ✅ Less manual maintenance

**Cons:**
- ❌ Code generation adds build complexity
- ❌ Generated code may need customization
- ⚠️ Harder to debug generated code
- ⚠️ `@default@` substitution still needs custom code

**When to use:**
- Schema shared across multiple languages/tools
- Large, complex schemas
- Want to enforce schema consistency

---

### Alternative 3: Interface-based Approach

Define interfaces for extensibility:

```go
type Validator interface {
    Validate() error
}

type Model struct {
    Title string
    Sites map[string]Site
    Steps []Step
}

func (m *Model) Validate() error {
    if m.Title == "" {
        return fmt.Errorf("missing required field: title")
    }
    
    for name, site := range m.Sites {
        if err := site.Validate(); err != nil {
            return fmt.Errorf("site %s: %w", name, err)
        }
    }
    
    return nil
}

type Site struct {
    Platform  string
    Namespace string
    Env       map[string]string
}

func (s *Site) Validate() error {
    validPlatforms := []string{"kubernetes", "podman", "docker", "linux"}
    if !contains(validPlatforms, s.Platform) {
        return fmt.Errorf("invalid platform: %s", s.Platform)
    }
    
    if s.Platform == "kubernetes" && s.Namespace == "" {
        return fmt.Errorf("kubernetes sites require namespace")
    }
    
    return nil
}
```

**Pros:**
- ✅ Extensible through interfaces
- ✅ Clear separation of concerns
- ✅ No dependencies
- ✅ Easy to test

**Cons:**
- ⚠️ More verbose than struct tags
- ⚠️ Validation code separate from struct definition
- ⚠️ Still need manual YAML parsing

**When to use:**
- Need validation flexibility
- Building extensible system
- Want testable validation logic

---

### Go Recommendation

**Keep the current manual parsing approach with minor enhancements:**

The current implementation is **excellent** for this use case because:
- Zero dependencies (core value)
- Full control for `@default@` substitution
- Explicit and debuggable
- Type-safe

**Suggested improvements (no new dependencies):**

1. **Extract parsing helpers into reusable functions:**
```go
// utils/parsing.go
func GetString(m map[string]interface{}, key string) string {
    if v, ok := m[key].(string); ok {
        return v
    }
    return ""
}

func GetStringWithDefault(m map[string]interface{}, key, defaultValue string) string {
    if v, ok := m[key].(string); ok {
        return v
    }
    return defaultValue
}

func GetBool(m map[string]interface{}, key string, defaultValue bool) bool {
    if v, ok := m[key].(bool); ok {
        return v
    }
    return defaultValue
}
```

2. **Add helper for `@default@` substitution:**
```go
func ApplyDefaultText(value, defaultText string) string {
    if strings.Contains(value, "@default@") {
        return strings.ReplaceAll(value, "@default@", strings.TrimSpace(defaultText))
    }
    return value
}
```

3. **Consider adding struct tags for documentation (not enforcement):**
```go
type Model struct {
    Title    string `yaml:"title" doc:"Example title (required)"`
    Subtitle string `yaml:"subtitle,omitempty" doc:"Optional subtitle"`
    // Tags document intent but don't enforce validation
}
```

**Only adopt validation libraries if:**
- You want declarative validation
- You're okay with external dependencies
- Standard YAML parsing (no custom `@default@` logic)

---

## Cross-Language Considerations

### Schema Consistency

Both Python and Go implementations should validate the same YAML files. Consider:

1. **Shared test fixtures:**
   - Use `tests/fixtures/skewer.yaml` for both implementations
   - Ensure both reject/accept the same invalid/valid files

2. **Documentation as source of truth:**
   - Keep `README.md` schema documentation canonical
   - Python and Go implementations follow the spec, not each other

3. **Validation parity:**
   - Both must reject unknown attributes
   - Both must validate platform values the same way
   - Both must handle `@default@` substitution identically

### Testing Strategy

```bash
# Validate both implementations produce identical results
python -m sketcher resolve test.yaml -o python-output.yaml
./sketcher-go resolve test.yaml -o go-output.yaml
diff python-output.yaml go-output.yaml

# Both should accept/reject the same files
for f in tests/fixtures/*.yaml; do
    python -m sketcher generate "$f" > /dev/null 2>&1
    PYTHON_EXIT=$?
    
    ./sketcher-go generate "$f" > /dev/null 2>&1
    GO_EXIT=$?
    
    if [ $PYTHON_EXIT -ne $GO_EXIT ]; then
        echo "MISMATCH: $f (Python: $PYTHON_EXIT, Go: $GO_EXIT)"
    fi
done
```

### Future: JSON Schema for Validation

If you want strict schema enforcement across both languages:

1. Define `sketcher-schema.json` (JSON Schema draft-07)
2. Python: Use `jsonschema` library for validation
3. Go: Use `github.com/xeipuuv/gojsonschema`
4. Both validate YAML against the same schema

**Example:**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Skewer YAML Schema",
  "type": "object",
  "required": ["title", "sites", "steps"],
  "additionalProperties": false,
  "properties": {
    "title": {
      "type": "string",
      "description": "Example title"
    },
    "sites": {
      "type": "object",
      "additionalProperties": {
        "$ref": "#/definitions/Site"
      }
    }
  },
  "definitions": {
    "Site": {
      "type": "object",
      "required": ["platform"],
      "properties": {
        "platform": {
          "enum": ["kubernetes", "podman", "docker", "linux"]
        }
      }
    }
  }
}
```

This is **optional** and adds complexity, but ensures perfect consistency.

---

## Summary

| Language | Recommendation | Why |
|----------|---------------|-----|
| **Python** | Keep current property descriptors | Zero dependencies, proven, simple |
| **Go** | Keep current manual parsing | Full control, zero dependencies, explicit |
| **Both** | Add type hints/comments | Better IDE support, no new dependencies |
| **Future** | Consider JSON Schema | Only if cross-tool validation needed |

**The current implementations are production-ready.** Don't fix what isn't broken—both approaches are well-suited to their language ecosystems and project constraints.

---

## JSON Schema Implementation

A comprehensive JSON Schema has been created at `skewer-schema.json` for:
- External tool integration
- IDE autocomplete (via YAML language servers)
- Documentation generation
- CI/CD validation

### Using the JSON Schema

**Python validation (recommended):**
```bash
# Install dependencies
pip install jsonschema

# Validate single file
python scripts/validate-schema.py skewer.yaml

# Validate multiple files
python scripts/validate-schema.py examples/*.yaml

# Example output
examples/skewer.yaml  ✓ Valid
tests/fixtures/*.yaml ✓ Valid

✓ All 5 file(s) valid
```

**Go validation:**
```bash
# Install dependencies
go get github.com/xeipuuv/gojsonschema
go get gopkg.in/yaml.v3

# Build validator
go build -o validate-schema scripts/validate-schema.go

# Validate files
./validate-schema skewer.yaml
./validate-schema examples/*.yaml
```

**Shell script (basic check):**
```bash
# Requires: yq, jq
./scripts/validate-schema.sh skewer.yaml
```

### IDE Integration

Add to `.vscode/settings.json` for YAML autocomplete:
```json
{
  "yaml.schemas": {
    "./skewer-schema.json": ["**/skewer.yaml", "**/skewer-*.yaml"]
  }
}
```

### Schema Features

The JSON Schema (`skewer-schema.json`) validates:

- ✅ Required fields: `title`, `sites`, `steps`
- ✅ Platform values: `kubernetes`, `podman`, `docker`, `linux`
- ✅ Kubernetes sites require `namespace` and `KUBECONFIG`
- ✅ Podman/Docker/Linux sites require `SKUPPER_PLATFORM`
- ✅ Command `apply` field: `readme` or `test` only
- ✅ Namespace naming convention (Kubernetes DNS-1123)
- ✅ Port range validation (1-65535)
- ✅ Unknown fields rejected (`additionalProperties: false`)
- ✅ Conditional validation (if platform=kubernetes, then namespace required)

### Integration with Current Code

The JSON Schema is **optional** and does not replace current validation:

```python
# Current code continues to work unchanged
model = Model("skewer.yaml")
model.check()  # Existing validation

# Optional: Pre-validate with JSON Schema
import jsonschema
schema = json.load(open("skewer-schema.json"))
data = yaml.safe_load(open("skewer.yaml"))
jsonschema.validate(data, schema)  # Extra validation layer
```

The schema provides **stricter** validation than current `.check()` methods:
- Rejects unknown fields immediately
- Validates enum values at parse time
- Provides detailed error messages with field paths

This is beneficial for catching typos and configuration errors early.
