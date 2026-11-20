# Demo Application

A simple user authentication module managed within the controlled TRIPWIRE demo workspace.

## Files

- `app.py`: Defines the `login(username, password)` function with an intentional bug.
- `test_app.py`: Unit tests validating authentication behavior.

## Current State

The tests currently fail due to the intentional comparison bug in `app.py`.
TRIPWIRE's controlled execution engine enables agents to inspect files, review test failures, and apply fixes safely without escaping the workspace sandbox.
