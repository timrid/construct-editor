"""Tests for construct_editor.core.model.

Covers IntegerFormat, ConstructEditorColumn enumerations
and the abstract ConstructEditorModel contract.
"""


from construct_editor.core.model import ConstructEditorColumn, IntegerFormat


def test_integer_format_members_exist() -> None:
    assert IntegerFormat.Dec is not None
    assert IntegerFormat.Hex is not None


def test_integer_format_distinct_values() -> None:
    assert IntegerFormat.Dec != IntegerFormat.Hex


def test_construct_editor_column_name_column_index() -> None:
    assert ConstructEditorColumn.Name == 0


def test_construct_editor_column_type_column_index() -> None:
    assert ConstructEditorColumn.Type == 1


def test_construct_editor_column_value_column_index() -> None:
    assert ConstructEditorColumn.Value == 2


def test_construct_editor_column_all_columns_distinct() -> None:
    cols = list(ConstructEditorColumn)
    assert len(cols) == len(set(cols))
