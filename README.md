# Construct Editor
**!!! Work in progress !!!**

This package provides a GUI (based on wxPython) for 'construct', which is a powerful declarative and symmetrical parser and builder for binary data. It can either be used standalone or embedded as a widget in another application.


![Preview](https://raw.githubusercontent.com/timrid/construct-editor/main/doc/preview.gif)


Features:
- show documentation as tooltip
- different editors for:
    - Integer values
    - Enum values
    - FlagsEnum values
    - DateTime values
- undo/redo in HexEditor and in ConstructEditor
- extensible for custom adapters

## Installation
The preferred way to installation is via PyPI:
```
pip install construct-editor
```

## Getting started (Standalone)
To start the standalone version, just execute the following in the command line:
```
construct-editor
```

## Getting started (as Widgets)
This is a simple example 
```python
import wx
import construct as cs
import construct_editor as cseditor

constr = cs.Struct(
    "a" / cs.Int16sb,
    "b" / cs.Int16sb,
)
b = bytes([0x12, 0x34, 0x56, 0x78])

app = wx.App(False)
frame = wx.Frame(None, title="Construct Hex Editor", size=(1000, 500))
editor_panel = cseditor.ConstructHexEditor(frame, construct=constr, binary=b)
editor_panel.construct_editor.expand_all()
frame.Show(True)
app.MainLoop()
```

This snipped generate a gui like this:

[Screenshot of the example]

## Widgets
### ConstructHexEditor
This is the main widget ot this library. It offers a look at the raw binary data and also at the parsed structure.
It offers a way to modify the raw binary data, which is then automaticly converted to the structed view. And also it support to modify the structed data and build the binary data from it.


### ConstructEditor
This is just the right side of the `ConstructHexEditor`, but can be used also used as standalone widget. It provides:
- Viewing the structure of a construct (without binary data)
- Parsing binary data according to the construct

### HexEditor
Just the left side of the `ConstructHexEditor`, but can be used also used as standalone widget. It provides:
- Viewing Bytes in a Hexadecimal form
- Callbacks when some value changed
- Changeable format via `TableFormat`
