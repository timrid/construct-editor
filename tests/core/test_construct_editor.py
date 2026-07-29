"""Tests for construct_editor.core.construct_editor — ConstructEditor (abstract base).

ConstructEditor is an abstract base class that requires a UI-framework-specific
subclass. These tests exercise only the framework-agnostic logic (parse/build
cycle, expand/collapse helpers, etc.) by using a minimal in-process stub.
"""

import pytest

# TODO: Implement a minimal stub of ConstructEditor (without wx) to test the
#       framework-agnostic methods once the concrete dependencies are clearer.
#
# Intended test scenarios:
#   - change_construct() triggers a re-parse
#   - parse() populates the model
#   - build() round-trips parsed data back to bytes
#   - change_hide_protected() toggles visibility of protected fields
#   - expand_all() / collapse_all() flip row_expanded on every entry
#   - expand_level(n) expands entries up to depth n
#   - copy/paste clipboard helpers delegate to _put_to_clipboard / _get_from_clipboard


@pytest.mark.skip(reason="Stub for ConstructEditor not yet implemented")
def test_placeholder() -> None:
    pass
