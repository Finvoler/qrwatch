# Milestone 5: Dry-Run And QQ Mail Notifier

Status: completed.

Goal: implement the first notification provider interface with safe dry-run
behavior and a QQ Mail-compatible SMTP provider.

Plan:

- Extend configuration with SMTP settings read from local env/config sources.
- Define a notifier result contract and event dispatch method.
- Keep dry-run as the default provider behavior.
- Implement an email notifier using Python SMTP libraries with QQ Mail-friendly
  defaults.
- Dispatch only deduplicated notification events.
- Test real-provider code with fake SMTP clients only.
- Update durable docs with required local variables and safety notes.

Validation:

- `conda run -n qrwatch python -m pytest`
- `python tools/validate_harness_structure.py`
