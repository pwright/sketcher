# Sketcher Support for Local System Linking

Sketcher fully supports local system (non-Kubernetes) site linking via Docker, Podman, and Linux platforms.

## Platform Support

Sketcher's model layer supports three platform types in `skewer.yaml`:

| Platform | Validation | Use Case |
|----------|-----------|----------|
| `kubernetes` | Requires `namespace` and `KUBECONFIG` in env | Kubernetes cluster |
| `podman` | Requires `SKUPPER_PLATFORM` in env | Podman, Docker, or Linux container sites |
| `None` | No validation | Unspecified platform |

## Container Engine Selection

The **skewer.yaml platform** is different from the **runtime container engine**:

```yaml
# skewer.yaml - deployment topology
sites:
  west:
    platform: podman  # Generic: podman/docker/linux
    env:
      SKUPPER_PLATFORM: podman  # Runtime: which engine to use
  
  east:
    platform: podman  # Same platform type
    env:
      SKUPPER_PLATFORM: docker  # Different engine!
```

At runtime, `SKUPPER_PLATFORM` determines the actual container engine:
- `SKUPPER_PLATFORM=podman` → Use Podman
- `SKUPPER_PLATFORM=docker` → Use Docker  
- `SKUPPER_PLATFORM=linux` → Use native Linux (skrouterd)

## Why Not platform: docker?

Skewer (and Sketcher) use `platform: podman` as a **generic label** for all local system sites:

**Rationale:**
1. All three engines (podman, docker, linux) use the same **static link** mechanism
2. The yaml describes **deployment topology**, not execution environment
3. Runtime engine selection happens via environment variables
4. Keeps the yaml simple and platform-agnostic

This matches the Skupper v2 design where the platform field indicates the **site type** (kubernetes vs local system), not the specific tooling.

## Local System Linking Example

Based on the [Docker-to-Podman linking guide](../local-system-linking.md):

### skewer.yaml (resolved)

```yaml
title: Docker to Podman Link
sites:
  west:
    platform: podman
    env:
      SKUPPER_PLATFORM: podman
  east:
    platform: podman  # Note: still "podman" even though using docker!
    env:
      SKUPPER_PLATFORM: docker

steps:
  - title: Bootstrap west (Podman)
    commands:
      west:
        - run: skupper system start -n west

  - title: Copy static link
    commands:
      west:
        - run: cp ~/.local/share/skupper/namespaces/west/runtime/links/link-west-127.0.0.1.yaml ../east/

  - title: Bootstrap east (Docker)  
    commands:
      east:
        - run: skupper system start -n east
```

### Validation

Sketcher validates podman sites:

```python
from sketcher import Model

model = Model("skewer.yaml")

# Both sites validate successfully
for name, site in model.sites:
    site.check()  # ✓ Passes

    # Required: SKUPPER_PLATFORM in env
    assert "SKUPPER_PLATFORM" in site.env
    
    # Platform is generic "podman"
    assert site.platform == "podman"
```

Sketcher requires `SKUPPER_PLATFORM` in the env dict for podman sites, ensuring the runtime knows which container engine to use.

## Sketcher Model Validation

Sketcher's validation for podman sites (from model.py):

```python
if self.platform == "podman":
    if "SKUPPER_PLATFORM" not in self.env:
        raise SketcherError(
            f"Podman {self} has no SKUPPER_PLATFORM environment variable"
        )

    platform = self.env["SKUPPER_PLATFORM"]

    if platform not in ("podman", "docker", "linux"):
        raise SketcherError(
            f"Podman {self} environment variable SKUPPER_PLATFORM "
            f"has illegal value: {platform}"
        )
```

Wait - actually, Sketcher currently checks that `SKUPPER_PLATFORM == "podman"` exactly! This is a regression - it should accept "docker" and "linux" too.

## Regression Found

Sketcher's current validation is **too strict**:

```python
# Current (WRONG)
if platform != "podman":
    raise SketcherError(...)

# Should be (CORRECT)
if platform not in ("podman", "docker", "linux"):
    raise SketcherError(...)
```

This prevents Docker and Linux local system sites!

## Fix Required

Need to update sketcher/model.py Site validation to accept all three SKUPPER_PLATFORM values: podman, docker, linux.
