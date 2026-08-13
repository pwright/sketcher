# Sketcher Behavioral Compatibility

This document explains how Sketcher maintains compatibility with Skewer's behavior, including subtle details that could cause regressions.

## Behavioral Fixes Applied

### 1. `apply_kubeconfigs` - Kubernetes Sites Only

**Issue:** Sketcher initially applied kubeconfigs to ALL sites, but Skewer only applies them to kubernetes sites.

**Impact:** Mixed kubernetes/podman deployments would break (podman sites would incorrectly get KUBECONFIG).

**Fix:**
```python
# Skewer (correct)
kube_sites = [x for _, x in model.sites if x.platform == "kubernetes"]

# Sketcher (initially wrong)
sites = list(model.sites)  # All sites!

# Sketcher (fixed)
kube_sites = [(name, site) for name, site in model.sites 
              if site.platform == "kubernetes"]
```

**Test:** `test_apply_kubeconfigs_mixed_platforms` verifies podman sites don't get KUBECONFIG.

**Reference:** skeleton/python/skewer/main.py:714-720

---

### 2. `object_property` - Always Substitute @default@

**Issue:** Sketcher initially only substituted `@default@` when `default is not None`, but Skewer does it for any string value.

**Impact:** Properties like `overview`, `summary`, `preamble`, `postamble` (with `default=None`) would never have `@default@` substituted.

**Fix:**
```python
# Skewer (correct)
if is_string(value):
    value = value.replace("@default@", str(nvl(default, "")).strip())

# Sketcher (initially wrong)
if isinstance(value, str) and default is not None:
    value = value.replace("@default@", str(default or "").strip())

# Sketcher (fixed)
if isinstance(value, str):
    value = value.replace("@default@", str(default or "").strip())
```

**Behavior:** Even if `default=None`, substitution happens (replaces with empty string).

**Example:**
```yaml
# User writes
overview: "@default@\n\nCustom overview"

# With default=None, should become
overview: "\n\nCustom overview"  # @default@ replaced with ""
```

**Reference:** skeleton/python/skewer/main.py:746-760

---

### 3. `capitalize()` - Preserve Case After First Character

**Issue:** Python's `str.capitalize()` lowercases all characters after the first, but Plano's `capitalize()` only uppercases the first.

**Impact:** Site names like "myNS" would become "Myns" instead of "MyNS" in generated READMEs.

**Fix:**
```python
# Python's str.capitalize() (wrong)
"myNS".capitalize()  # → "Myns"

# Plano's capitalize() (correct)
def capitalize(string):
    if not string:
        return ""
    return string[0].upper() + string[1:]

"myNS" → "MyNS"  # Preserves case
```

**Used in:** `Site.title` property when no explicit title is provided.

**Test:** `test_capitalize` in test_utils.py

**Reference:** skeleton/python/plano/main.py:1515-1519

---

### 4. `get_github_owner_repo` - Return Type

**Issue:** Skewer's `split()` returns a list, Sketcher initially wrapped in `tuple()`.

**Impact:** Low risk - unpacking works the same, but type differs.

**Fix:**
```python
# Both work for unpacking
owner, repo = get_github_owner_repo()

# But type differs
# Skewer: returns list
# Sketcher: returns tuple

# Fixed to be explicit
parts = path.split("/", 1)
return (parts[0], parts[1])  # Explicit tuple
```

**Note:** Documented in function docstring. No actual breakage since unpacking works identically.

**Reference:** skeleton/python/skewer/main.py:816-833

---

### 5. `__repr__` Formats - Error Messages

**Issue:** Sketcher initially used modern repr format like `Model(...)`, but Skewer uses `model '...'` format.

**Impact:** All error messages would have different text, making troubleshooting harder for Skewer users.

**Fix:**
```python
# Sketcher (initially wrong)
def __repr__(self):
    return f"Model('{self.yaml_file}')"

# Sketcher (fixed to match Skewer)
def __repr__(self):
    return f"model '{self.yaml_file}'"
```

**Applied to:** Model, Site, Step, Command classes

**Examples:**
- `model 'skewer.yaml'` (not `Model('skewer.yaml')`)
- `site 'west'` (not `Site('west')`)
- `step 1 'Deploy'` (not `Step(1, 'Deploy')`)
- `command 'kubectl get pods'` (not `Command('kubectl get pods')`)

**Why it matters:** These strings appear in exception messages throughout the codebase:
```python
raise SketcherError(f"{site} has no KUBECONFIG environment variable")
# → "site 'west' has no KUBECONFIG environment variable"
```

**Test:** `TestReprFormats` class verifies all repr formats match Skewer.

**Reference:** skeleton/python/skewer/main.py:876, 912, 964, 1005-1008

---

### 6. `SKUPPER_PLATFORM` Validation - Accept Docker and Linux

**Issue:** Sketcher initially only accepted `SKUPPER_PLATFORM=podman`, but Skupper v2 supports docker and linux too.

**Impact:** Docker and Linux local system sites would fail validation, breaking local-to-local linking.

**Fix:**
```python
# Sketcher (initially wrong)
if platform != "podman":
    raise SketcherError(...)

# Sketcher (fixed)
if platform_value not in ("podman", "docker", "linux"):
    raise SketcherError(
        f"... Must be one of: podman, docker, linux"
    )
```

**Why it matters:** Local system linking (non-Kubernetes) supports three container engines:
- `SKUPPER_PLATFORM=podman` → Podman container engine
- `SKUPPER_PLATFORM=docker` → Docker container engine  
- `SKUPPER_PLATFORM=linux` → Native Linux (skrouterd binary)

All three use the same **static link** mechanism for site-to-site connections.

**Example usage:**
```yaml
# Mixed docker + podman deployment
sites:
  west:
    platform: podman  # Generic platform type
    env:
      SKUPPER_PLATFORM: podman  # Specific engine
  
  east:
    platform: podman  # Same platform type
    env:
      SKUPPER_PLATFORM: docker  # Different engine!
```

**Test:** `test_site_validation_podman_platforms` verifies all three engines validate.

**Reference:** 
- local-system-linking.md (Docker-to-Podman example)
- skeleton/python/skewer/main.py:940-948 (Skewer doesn't validate SKUPPER_PLATFORM value)

---

## Testing Strategy

All behavioral compatibility issues have corresponding tests:

| Fix | Test |
|-----|------|
| apply_kubeconfigs (kubernetes only) | `test_apply_kubeconfigs_mixed_platforms` |
| @default@ always substitutes | `test_default_text_substitution` |
| capitalize() preserves case | `test_capitalize` |
| repr formats | `TestReprFormats` class (4 tests) |

**Total:** 60/60 tests passing (includes 7 new behavioral tests)

---

## Migration Notes

When migrating from Skewer to Sketcher:

1. ✅ **No code changes needed** - Sketcher maintains behavioral compatibility
2. ✅ **Error messages match** - Same repr formats
3. ✅ **Mixed platforms work** - Kubeconfigs only on kubernetes sites
4. ✅ **Site titles match** - capitalize() preserves case
5. ✅ **@default@ works** - Even with None defaults

The only change is using resolved yaml files (via `sketcher resolve`).

---

## References

All fixes reference the original Skewer code:

- **apply_kubeconfigs:** main.py:714-720
- **object_property:** main.py:835-845
- **capitalize:** plano/main.py:1515-1519
- **get_github_owner_repo:** main.py:816-833
- **__repr__ formats:** main.py:876, 912, 964, 1005-1008

These line numbers are from `/home/paulwright/repos/sk/skeletal/skeleton/python/skewer/`.

**Note:** Never edit files in the `skeleton/` symlink - it points to legacy version for reference only.
