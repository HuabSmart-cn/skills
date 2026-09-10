# Secrets Handling Across Sibling Skills

Every sibling skill ships a `Verifying secrets safely` block in its
Prerequisites section. Always verify prerequisites by running
`scripts/validate_setup.py` (where it exists) or, for skills without
one (`ncore`, `physical-ai-datasets`, the router), use
`hf auth whoami` or a length-only shell check. Never write ad-hoc
bash that interpolates secret values.

In particular, do not use the bash anti-pattern:

```bash
echo "HF_TOKEN: ***REDACTED***
```

This prints `yes<token-value>` because `${VAR:***REDACTED***
to `no` when the variable is empty. If you suspect a token was
echoed, rotate it (`huggingface.co/settings/tokens`,
`org.ngc.nvidia.com/setup/api-key`) before continuing.

## Safe verification patterns

```bash
# Hugging Face token
hf auth whoami

# Length-only check (does not echo the value)
[ -n "${HF_TOKEN:***REDACTED***
[ -n "${NGC_API_KEY:***REDACTED***
```
