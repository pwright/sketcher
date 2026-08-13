# Migration from Skewer

If you have existing Skewer YAML files that use `standard:` step references, use the `skewer resolve` command to expand them into explicit YAML.

## Using the Resolver

```bash
# Expand standard steps
skewer resolve old-skewer.yaml -o new-skewer.yaml

# Or modify in-place
skewer resolve skewer.yaml --in-place

# Batch process multiple files
for f in examples/*/skewer.yaml; do
  skewer resolve "$f" --in-place
done
```

## Why Explicit YAML?

Sketcher uses fully expanded YAML instead of runtime step expansion because:

- **Clearer behavior** - No hidden magic, what you see is what runs
- **Easier debugging** - All commands visible in the YAML file
- **Better git diffs** - Changes are explicit in version control
- **Simpler code** - No complex runtime expansion logic

## Migration Results

Batch migration results from real Skupper examples:

- ✅ 19/30 real Skupper examples resolved (63%)
- ✅ 100% success rate on modern examples (2024+)
- ⚠️ Failures only on very old yamls with unprefixed step names

For new examples, use the [common step patterns](../user-guide/common-patterns.md) rather than relying on a standard steps library.

## After Migration

Once you've resolved your YAML files:

1. **Test the migration**: Run `sketcher demo` to verify the expanded YAML works
2. **Review the changes**: Check git diffs to understand what was expanded
3. **Update documentation**: Regenerate README with `skewer generate`
4. **Commit the changes**: Commit the explicit YAML to version control

## Compatibility Notes

See [Compatibility](compatibility.md) for detailed information about:

- Skupper v1 vs v2 syntax changes
- Platform-specific considerations
- Known issues and workarounds

## Next Steps

- Learn about [Common Patterns](../user-guide/common-patterns.md) for new examples
- See the [Configuration](../configuration/json-schema-quickstart.md) guide for schema validation
- Explore [Use Cases](../user-guide/use-cases.md) for platform-specific workflows
