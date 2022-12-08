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

## Example of custom population of the gallery frame

The following example shows how to build a full gallery frame, including comments.

The `ConstructGalleryFrame` class is used to build the frame in place of the `wx.Frame` used in the previous example.

`ConstructGalleryFrame` parameters:

- `gallery_selection`: default selection (shall not point to a comment)
- `construct_gallery`: dictionary of the names of the gallery elements (key) and `GalleryItem` (value). If the value is `None`, the element is considered a comment.
- `title`: title of the app
- `size`: tuple defining the default app size (x, y)

`GalleryItem` parameters:

- `construct`: *construct* definition related to the gallery element
- `example_binarys`: dictionary of example names (key) and data (value) related to the gallery element

```python
import construct as cs
import wx
import construct_editor.main as csmain
import construct_editor.gallery as csgallery

# construct definitions

flags_struct = cs.Struct(
    "flag0" / cs.Flag,
    "flag1" / cs.Flag,

    "bit_struct" / cs.BitStruct(
        "bit_flag0" / cs.Flag,
        "bit_flag1" / cs.Flag,
        "bit_flag2" / cs.Flag,
        "bit_flag3" / cs.Flag,
        cs.Padding(4)
    )
)

pass_struct = cs.Struct(
    "value1" / cs.Int8sb,
    "pass" / cs.Pass,
    "value2" / cs.Int8sb,
)

padded_struct = cs.Struct(
    "padded" / cs.Padded(5, cs.Bytes(3)),
    "padding" / cs.Padding(5),
)

# app setup

app = wx.App(False)
frame = csmain.ConstructGalleryFrame(
            None,
            gallery_selection=0,
            
            # Gallery definition
            construct_gallery = {
                "Test: Flag": csgallery.GalleryItem(
                    construct=flags_struct,
                    example_binarys={
                        "1": bytes([0x01, 0x02, 0x40]),
                        "Zeros": bytes(3),
                    },
                ),
                "## miscellaneous ##########################": None,
                "Test: Pass": csgallery.GalleryItem(
                    construct=pass_struct,
                    example_binarys={
                        "Zeros": bytes(2),
                        "1": b"12",
                    },
                ),
                "Test: Padded": csgallery.GalleryItem(
                    construct=padded_struct,
                    example_binarys={
                        "1": bytes([0, 1, 2, 3, 4, 0xF1, 0xF2, 0xF3, 0xF4, 0xF5]),
                        "Zeros": bytes(10),
                    },
                )
            },

            title="Custom sample",
            size=(1000, 500)
)
frame.Show(True)
app.MainLoop()
```

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
