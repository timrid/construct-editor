# Changelog
## [Unreleased]
Complete refactoring of the code, so that core components of the construct-editor are seperated vom GUI components. That makes it theoretically possible to add multiple GUI frameworks in the future. Besides this the following notable enhancements are implemented:
- Any keypress of an printable key will start editing an item. No ENTER or double click is reqired any more.
- Protected entries (starting with _) are not visible in list view if "hide protected" is activated. (#13)
- Implemented checkbox for `cs.Flag`
- Fixed bug with PaddedString (#14)
- Added module "construct_editor.core.custom" for easier addition of custom constructs.

-------------------------------------------------------------------------------
## [0.0.19] - 2022-09-07
Enhanced ConstructHexEditor:
- Fixed a bug which leads to an "Fatal Python error" as of wxPython 4.2.

-------------------------------------------------------------------------------
## [0.0.18] - 2022-09-07
General:
- Package is now also compatible with Python 3.9 and 3.10

Enhanced ConstructHexEditor:
- Fixed a bug which leads to an exception as of wxPython 4.2.

-------------------------------------------------------------------------------
## [0.0.17] - 2022-08-03
Enhanced ConstructEditor:
- Fixed a bug in conditional constructs (IfThenElse/Switch/FocusedSeq/Select)

-------------------------------------------------------------------------------
## [0.0.16] - 2022-05-11
Enhanced ConstructEditor:
- Added support for
   - `cs.NullStripped`
   - `cs.NullTerminated`
   - `cs.StringEncoded`
   - `cs.BitsSwapped`
   - `cs.Const`
   - `cs.FocusedSeq`
   - `cs.Select`
- Fixed issue: When the users has opened an DVC Editor and clicks somewhere else, the Object-Editor is now closed correcty.
- Fixed issue: Removed recursion bug inside conditional constructs (`cs.IfThenElse`, `cs.Switch`, ...).

Enhanced HexEditor:
- Added thousands separator for byte/bit positions.
- Display `x Bits` insted of `x Bytes` if we are inside a `cs.Bitwise`.
- Fixed issue: When 0 or a multiple of 16 Bytes are shown in the hex editor, then there is no new line for adding data. This is now fixed, and an new line is added.

-------------------------------------------------------------------------------
## [0.0.15] - 2022-01-20
Enhanced ConstructHexEditor:
- added support for `cs.Default`: when right clicking an object with default value the option "Set to default" is availabe
- fixed issue: when sub-hex-panels are created (eg. for bitwiese data), the data is not visible in the root-hex-panel when selecting an item.
- fixed issue: the GUI can completely crash, when the building/parsing takes its time and the user slowly double clicks somewhere else in the DataViewControl

-------------------------------------------------------------------------------
## [0.0.14] - 2021-07-29
Enhanced ConstructHexEditor:
- fixed issue: When the another binary data was set, then the old HexEditors were still displayed.

-------------------------------------------------------------------------------
## [0.0.13] - 2021-07-29
Enhanced ConstructHexEditor:
- fixed stream issues: When selecting the root element, not all data was marked in the HexEditor.

-------------------------------------------------------------------------------
## [0.0.12] - 2021-07-25
Enhanced ConstructEditor:
- added `cs.Compressed`, `cs.Prefixed`
- show Infos about the construct object, when hovering over the type in the DVC
- changed "->" to "." as path seperator

Enhanced HexEditor:
- added read_only mode

Enhanced ConstructHexEditor:
- Show multiple HexEditor's when nested streams are used. This is a usefull feature, if the construct switches from byte- to bit-level to see the single bits. Or when using `cs.Tunnel` for `cs.Compressed` or encryption. So you can see also the uncompressed/decrypted data.

-------------------------------------------------------------------------------
## [0.0.11] - 2021-07-20
Enhanced ConstructEditor:
- added `cs.Checksum`

-------------------------------------------------------------------------------
## [0.0.10] - 2021-07-16
Enhanced ConstructEditor:
- the enter key (in the number block) can be used to finish editing a construct entry
- added `cs.FixedSized` #8 
- changed `cs.Timestamp` a little bit #10 
- fixed wrong Byte-Position in constructs with nested streams #9 

-------------------------------------------------------------------------------
## [0.0.9] - 2021-06-27
Enhanced ConstructEditor:
- multiple speed optimizations for large Arrays
- added support for `cs.Flag`
- replaces "Expand/Collapse all" with "Expand/Collapse children" in the Context menu, which are now only available for `cs.Struct` and `cs.Array`

-------------------------------------------------------------------------------
## [0.0.8] - 2021-06-17
Enhanced ConstructEditor:
- fixing bug, when root construct is a GreedyRange and the "List View" is used
- name of root construct is added to the path

-------------------------------------------------------------------------------
## [0.0.7] - 2021-06-16
Enhanced ConstructEditor:
- added support for `cs.GreedyBytes`
- `cs.Bytes` and `cs.GreedyBytes` are now changeable in the ConstructEditor
- when an object in the ConstructEditor is changed and the binary data is recalculated, then the binary data is parsed again, to recalculate all values that may depend on the changed object (eg. for `cs.Peek`)
- fixed dependency error. wxPython>=4.1.1 is needed. see #2
- `cs.GreedyRange` now also supports "List View"
- some other small bugfixes

-------------------------------------------------------------------------------
## [0.0.6] - 2021-05-24
- changed dependencies to `construct==2.10.67` and `construct-typing==0.5.0`
- changed class names according to `construct-typing==0.5.0`

-------------------------------------------------------------------------------
## [0.0.5] - 2021-05-19
Enhanced ConstructEditor:
- added `cs.Padded`, `cs.Padding` and `cs.Aligned`
- added "ASCII View" Button to ContextMenu for `cs.Bytes`
- fixed bug, when the root construct has a name
- fixed bug, when an exception was thrown, while trying to edit a read-only field

-------------------------------------------------------------------------------
## [0.0.4] - 2021-05-03
Enhanced ConstructEditor:
- edit entrys directly in the DataViewCtrl
- show docs directly in the DataViewCtrl as Tooltip
- show byte position, offset and the path to the selected object in a StatusBar
- added undo/redo
- added a ListView for `cs.Array`
- added shortcuts for copy/paste/expand/collapse
- added the possibility to add custom `cs.Adapter` constructs to the GUI

Enhanced ConstructHexEditor:
- HexEditor Panel can be collapsed to make the ConstructEditor larger

-------------------------------------------------------------------------------
## [0.0.3] - 2021-04-14
reduce wxPython dependency to >=4.1.0

-------------------------------------------------------------------------------
## [0.0.2] - 2021-04-11
Enhanced HexEditor:
- corrected selection of a byte sequence
- added cut/copy/paste of byte sequences
- added undo/redo
- added status bar to show the size and the current selection

-------------------------------------------------------------------------------
## [0.0.1] - 2021-04-05
Initial Version