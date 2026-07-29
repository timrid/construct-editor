"""Tests for construct_editor.core.custom — custom construct registration API.

Covers add_custom_transparent_subconstruct, add_custom_tunnel, and
add_custom_adapter without any wx dependency.
"""

import construct_typed as cst

from construct_editor.core.custom import (
    add_custom_adapter,
    add_custom_transparent_subconstruct,
    add_custom_tunnel,
)

# ---------------------------------------------------------------------------
# add_custom_transparent_subconstruct
# ---------------------------------------------------------------------------


def test_add_custom_transparent_subconstruct_registration_does_not_raise() -> None:
    """Calling add_custom_transparent_subconstruct must not raise."""

    class MySubconstruct(cst.Subconstruct[bytes, bytes, bytes, bytes]):
        pass

    # Should not raise even if called multiple times
    add_custom_transparent_subconstruct(MySubconstruct)


# TODO: Verify that include_metadata correctly wraps the custom subconstruct
#       after registration and that parse/build still round-trips correctly.


# ---------------------------------------------------------------------------
# add_custom_tunnel
# ---------------------------------------------------------------------------


def test_add_custom_tunnel_registration_does_not_raise() -> None:
    """Calling add_custom_tunnel must not raise."""

    class MyTunnel(cst.Tunnel[bytes, bytes]):
        def _decode(self, data, context, path):  # type: ignore[override]
            return data

        def _encode(self, data, context, path):  # type: ignore[override]
            return data

    add_custom_tunnel(MyTunnel, type_str="MyTunnel")


# TODO: Verify that byte_range metadata is propagated through the tunnel.


# ---------------------------------------------------------------------------
# add_custom_adapter
# ---------------------------------------------------------------------------


def test_add_custom_adapter_registration_does_not_raise() -> None:
    """Calling add_custom_adapter must not raise."""
    from construct_editor.core.custom import AdapterObjEditorType

    class MyAdapter(cst.Adapter[bytes, bytes, bytes, bytes]):
        def _decode(self, obj, context, path):  # type: ignore[override]
            return obj

        def _encode(self, obj, context, path):  # type: ignore[override]
            return obj

    add_custom_adapter(MyAdapter, type_str="MyAdapter", obj_editor_type=AdapterObjEditorType.Default)


# TODO: Verify correct ObjViewSettings are chosen for the adapter after registration.
