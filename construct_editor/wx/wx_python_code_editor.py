#!/usr/bin/env python

import keyword

import sys
import wx
import wx.stc as stc

# import images

# ----------------------------------------------------------------------

demoText = """\
## This version of the editor has been set up to edit Python source
## code.  Here is a copy of wxPython/demo/Main.py to play with.


"""

# ----------------------------------------------------------------------


faces = {
    "times": "Times New Roman",
    "mono": "Courier New",
    # "helv": "Arial",
    "helv": "Consolas",
    "other": "Comic Sans MS",
    "size": 10,
    "size2": 8,
}


# ----------------------------------------------------------------------


class PythonSTC(stc.StyledTextCtrl):
    def __init__(self, parent, ID, text="", pos=wx.DefaultPosition, size=wx.DefaultSize, style=0):
        stc.StyledTextCtrl.__init__(self, parent, ID, pos, size, style)

        self.CmdKeyAssign(ord("B"), stc.STC_SCMOD_CTRL, stc.STC_CMD_ZOOMIN)
        self.CmdKeyAssign(ord("N"), stc.STC_SCMOD_CTRL, stc.STC_CMD_ZOOMOUT)

        self.SetLexer(stc.STC_LEX_PYTHON)
        self.SetKeyWords(0, " ".join(keyword.kwlist))

        self.SetProperty("fold", "1")
        self.SetProperty("tab.timmy.whinge.level", "1")
        self.SetMargins(0, 0)

        self.SetViewWhiteSpace(False)
        # self.SetBufferedDraw(False)
        # self.SetViewEOL(True)
        # self.SetEOLMode(stc.STC_EOL_CRLF)
        # self.SetUseAntiAliasing(True)

        self.SetEdgeMode(stc.STC_EDGE_BACKGROUND)
        self.SetEdgeColumn(78)

        # Setup a margin to hold fold markers
        # self.SetFoldFlags(16)  ###  WHAT IS THIS VALUE?  WHAT ARE THE OTHER FLAGS?  DOES IT MATTER?
        self.SetMarginType(2, stc.STC_MARGIN_SYMBOL)
        self.SetMarginMask(2, stc.STC_MASK_FOLDERS)
        self.SetMarginSensitive(2, True)
        self.SetMarginWidth(2, 12)

        # Fold Style: Like a flattened tree control using square headers
        self.MarkerDefine(stc.STC_MARKNUM_FOLDEROPEN, stc.STC_MARK_BOXMINUS, "white", "#808080")
        self.MarkerDefine(stc.STC_MARKNUM_FOLDER, stc.STC_MARK_BOXPLUS, "white", "#808080")
        self.MarkerDefine(stc.STC_MARKNUM_FOLDERSUB, stc.STC_MARK_VLINE, "white", "#808080")
        self.MarkerDefine(stc.STC_MARKNUM_FOLDERTAIL, stc.STC_MARK_LCORNER, "white", "#808080")
        self.MarkerDefine(stc.STC_MARKNUM_FOLDEREND, stc.STC_MARK_BOXPLUSCONNECTED, "white", "#808080")
        self.MarkerDefine(stc.STC_MARKNUM_FOLDEROPENMID, stc.STC_MARK_BOXMINUSCONNECTED, "white", "#808080")
        self.MarkerDefine(stc.STC_MARKNUM_FOLDERMIDTAIL, stc.STC_MARK_TCORNER, "white", "#808080")

        self.Bind(stc.EVT_STC_UPDATEUI, self.OnUpdateUI)
        self.Bind(stc.EVT_STC_MARGINCLICK, self.OnMarginClick)
        self.Bind(wx.EVT_KEY_DOWN, self.OnKeyPressed)

        # Make some styles,  The lexer defines what each style is used for, we
        # just have to define what each style looks like.  This set is adapted from
        # Scintilla sample property files.

        # Global default styles for all languages
        self.StyleSetSpec(stc.STC_STYLE_DEFAULT, "face:%(helv)s,size:%(size)d" % faces)
        self.StyleClearAll()  # Reset all to be like the default

        # Global default styles for all languages
        self.StyleSetSpec(stc.STC_STYLE_DEFAULT, "face:%(helv)s,size:%(size)d" % faces)
        self.StyleSetSpec(stc.STC_STYLE_LINENUMBER, "back:#C0C0C0,face:%(helv)s,size:%(size2)d" % faces)
        self.StyleSetSpec(stc.STC_STYLE_CONTROLCHAR, "face:%(other)s" % faces)
        self.StyleSetSpec(stc.STC_STYLE_BRACELIGHT, "fore:#FFFFFF,back:#0000FF,bold")
        self.StyleSetSpec(stc.STC_STYLE_BRACEBAD, "fore:#000000,back:#FF0000,bold")

        # Python styles
        # Default
        self.StyleSetSpec(stc.STC_P_DEFAULT, "fore:#000000,face:%(helv)s,size:%(size)d" % faces)
        # Comments
        self.StyleSetSpec(stc.STC_P_COMMENTLINE, "fore:#007F00,face:%(helv)s,size:%(size)d" % faces)
        # Number
        self.StyleSetSpec(stc.STC_P_NUMBER, "fore:#007F7F,size:%(size)d" % faces)
        # String
        self.StyleSetSpec(stc.STC_P_STRING, "fore:#7F007F,face:%(helv)s,size:%(size)d" % faces)
        # Single quoted string
        self.StyleSetSpec(stc.STC_P_CHARACTER, "fore:#7F007F,face:%(helv)s,size:%(size)d" % faces)
        # Keyword
        self.StyleSetSpec(stc.STC_P_WORD, "fore:#00007F,bold,size:%(size)d" % faces)
        # Triple quotes
        self.StyleSetSpec(stc.STC_P_TRIPLE, "fore:#7F0000,size:%(size)d" % faces)
        # Triple double quotes
        self.StyleSetSpec(stc.STC_P_TRIPLEDOUBLE, "fore:#7F0000,size:%(size)d" % faces)
        # Class name definition
        self.StyleSetSpec(stc.STC_P_CLASSNAME, "fore:#0000FF,bold,underline,size:%(size)d" % faces)
        # Function or method name definition
        self.StyleSetSpec(stc.STC_P_DEFNAME, "fore:#007F7F,bold,size:%(size)d" % faces)
        # Operators
        self.StyleSetSpec(stc.STC_P_OPERATOR, "bold,size:%(size)d" % faces)
        # Identifiers
        self.StyleSetSpec(stc.STC_P_IDENTIFIER, "fore:#000000,face:%(helv)s,size:%(size)d" % faces)
        # Comment-blocks
        self.StyleSetSpec(stc.STC_P_COMMENTBLOCK, "fore:#7F7F7F,size:%(size)d" % faces)
        # End of line where string is not closed
        self.StyleSetSpec(stc.STC_P_STRINGEOL, "fore:#000000,face:%(mono)s,back:#E0C0E0,eol,size:%(size)d" % faces)

        self.SetCaretForeground("BLUE")

        # register some images for use in the AutoComplete box.
        # self.RegisterImage(1, images.Smiles.GetBitmap())
        self.RegisterImage(2, wx.ArtProvider.GetBitmap(wx.ART_NEW, size=wx.Size(16, 16)))
        self.RegisterImage(3, wx.ArtProvider.GetBitmap(wx.ART_COPY, size=wx.Size(16, 16)))

        self.SetText(text)

    def OnKeyPressed(self, event):
        if self.CallTipActive():
            self.CallTipCancel()
        key = event.GetKeyCode()

        if key == 32 and event.ControlDown():
            pos = self.GetCurrentPos()

            # Tips
            if event.ShiftDown():
                self.CallTipSetBackground("yellow")
                self.CallTipShow(
                    pos,
                    "lots of of text: blah, blah, blah\n\n"
                    "show some suff, maybe parameters..\n\n"
                    "fubar(param1, param2)",
                )
            # Code completion
            else:
                # lst = []
                # for x in range(50000):
                #    lst.append('%05d' % x)
                # st = " ".join(lst)
                # print(len(st))
                # self.AutoCompShow(0, st)

                kw = list(keyword.kwlist)
                kw.append("zzzzzz?2")
                kw.append("aaaaa?2")
                kw.append("__init__?3")
                kw.append("zzaaaaa?2")
                kw.append("zzbaaaa?2")
                kw.append("this_is_a_longer_value")
                # kw.append("this_is_a_much_much_much_much_much_much_much_longer_value")

                kw.sort()  # Python sorts are case sensitive
                self.AutoCompSetIgnoreCase(False)  # so this needs to match

                # Images are specified with a appended "?type"
                for i in range(len(kw)):
                    if kw[i] in keyword.kwlist:
                        kw[i] = kw[i] + "?1"

                self.AutoCompShow(0, " ".join(kw))
        else:
            event.Skip()

    def OnUpdateUI(self, evt):
        # check for matching braces
        braceAtCaret = -1
        braceOpposite = -1
        charBefore = None
        styleBefore = None
        caretPos = self.GetCurrentPos()

        if caretPos > 0:
            charBefore = self.GetCharAt(caretPos - 1)
            styleBefore = self.GetStyleAt(caretPos - 1)

        # check before
        if charBefore and chr(charBefore) in "[]{}()" and styleBefore == stc.STC_P_OPERATOR:
            braceAtCaret = caretPos - 1

        # check after
        if braceAtCaret < 0:
            charAfter = self.GetCharAt(caretPos)
            styleAfter = self.GetStyleAt(caretPos)

            if charAfter and chr(charAfter) in "[]{}()" and styleAfter == stc.STC_P_OPERATOR:
                braceAtCaret = caretPos

        if braceAtCaret >= 0:
            braceOpposite = self.BraceMatch(braceAtCaret)

        if braceAtCaret != -1 and braceOpposite == -1:
            self.BraceBadLight(braceAtCaret)
        else:
            self.BraceHighlight(braceAtCaret, braceOpposite)
            # pt = self.PointFromPosition(braceOpposite)
            # self.Refresh(True, wxRect(pt.x, pt.y, 5,5))
            # print(pt)
            # self.Refresh(False)

    def OnMarginClick(self, evt):
        # fold and unfold as needed
        if evt.GetMargin() == 2:
            if evt.GetShift() and evt.GetControl():
                self.FoldAll()
            else:
                lineClicked = self.LineFromPosition(evt.GetPosition())

                if self.GetFoldLevel(lineClicked) & stc.STC_FOLDLEVELHEADERFLAG:
                    if evt.GetShift():
                        self.SetFoldExpanded(lineClicked, True)
                        self.Expand(lineClicked, True, True, 1)
                    elif evt.GetControl():
                        if self.GetFoldExpanded(lineClicked):
                            self.SetFoldExpanded(lineClicked, False)
                            self.Expand(lineClicked, False, True, 0)
                        else:
                            self.SetFoldExpanded(lineClicked, True)
                            self.Expand(lineClicked, True, True, 100)
                    else:
                        self.ToggleFold(lineClicked)

    def FoldAll(self):
        lineCount = self.GetLineCount()
        expanding = True

        # find out if we are folding or unfolding
        for lineNum in range(lineCount):
            if self.GetFoldLevel(lineNum) & stc.STC_FOLDLEVELHEADERFLAG:
                expanding = not self.GetFoldExpanded(lineNum)
                break

        lineNum = 0

        while lineNum < lineCount:
            level = self.GetFoldLevel(lineNum)
            if level & stc.STC_FOLDLEVELHEADERFLAG and (level & stc.STC_FOLDLEVELNUMBERMASK) == stc.STC_FOLDLEVELBASE:

                if expanding:
                    self.SetFoldExpanded(lineNum, True)
                    lineNum = self.Expand(lineNum, True)
                    lineNum = lineNum - 1
                else:
                    lastChild = self.GetLastChild(lineNum, -1)
                    self.SetFoldExpanded(lineNum, False)

                    if lastChild > lineNum:
                        self.HideLines(lineNum + 1, lastChild)

            lineNum = lineNum + 1

    def Expand(self, line, doExpand, force=False, visLevels=0, level=-1):
        lastChild = self.GetLastChild(line, level)
        line = line + 1

        while line <= lastChild:
            if force:
                if visLevels > 0:
                    self.ShowLines(line, line)
                else:
                    self.HideLines(line, line)
            else:
                if doExpand:
                    self.ShowLines(line, line)

            if level == -1:
                level = self.GetFoldLevel(line)

            if level & stc.STC_FOLDLEVELHEADERFLAG:
                if force:
                    if visLevels > 1:
                        self.SetFoldExpanded(line, True)
                    else:
                        self.SetFoldExpanded(line, False)

                    line = self.Expand(line, doExpand, force, visLevels - 1)

                else:
                    if doExpand and self.GetFoldExpanded(line):
                        line = self.Expand(line, True, force, visLevels - 1)
                    else:
                        line = self.Expand(line, False, force, visLevels - 1)
            else:
                line = line + 1

        return line


def GetCaretPeriod(win=None):
    """
    Attempts to identify the correct caret blinkrate to use in the Demo Code panel.

    :pram wx.Window win: a window to pass to wx.SystemSettings.GetMetric.

    :return: a value in milliseconds that indicates the proper period.
    :rtype: int

    :raises: ValueError if unable to resolve a proper caret blink rate.
    """
    if "--no-caret-blink" in sys.argv:
        return 0

    try:
        onmsec = wx.SystemSettings.GetMetric(wx.SYS_CARET_ON_MSEC, win)
        offmsec = wx.SystemSettings.GetMetric(wx.SYS_CARET_OFF_MSEC, win)

        # check values aren't -1
        if -1 in (onmsec, offmsec):
            raise ValueError("Unable to determine caret blink rate.")

        # attempt to average.
        # (wx systemsettings allows on and off time, but scintilla just takes a single period.)
        return int((onmsec + offmsec) / 2.0)

    except AttributeError:
        # Issue where wx.SYS_CARET_ON/OFF_MSEC is unavailable.
        raise ValueError("Unable to determine caret blink rate.")


class WxPythonCodeEditor(PythonSTC):
    def __init__(self, parent, ID, text="", pos=wx.DefaultPosition, size=wx.DefaultSize, style=0):
        PythonSTC.__init__(self, parent, ID, text, pos, size, style)
        self.SetUpEditor()

    # Some methods to make it compatible with how the wxTextCtrl is used
    def SetValue(self, value):
        # if wx.USE_UNICODE:
        # value = value.decode('iso8859_1')
        val = self.GetReadOnly()
        self.SetReadOnly(False)
        self.SetText(value)
        self.EmptyUndoBuffer()
        self.SetSavePoint()
        self.SetReadOnly(val)

    def SetEditable(self, val):
        self.SetReadOnly(not val)

    def IsModified(self):
        return self.GetModify()

    def Clear(self):
        self.ClearAll()

    def SetInsertionPoint(self, pos):
        self.SetCurrentPos(pos)
        self.SetAnchor(pos)

    def ShowPosition(self, pos):
        line = self.LineFromPosition(pos)
        # self.EnsureVisible(line)
        self.GotoLine(line)

    def GetLastPosition(self):
        return self.GetLength()

    def GetPositionFromLine(self, line):
        return self.PositionFromLine(line)

    def GetRange(self, start, end):
        return self.GetTextRange(start, end)

    def GetSelection(self):
        return self.GetAnchor(), self.GetCurrentPos()

    def SetSelection(self, start, end):
        self.SetSelectionStart(start)
        self.SetSelectionEnd(end)

    def SelectLine(self, line):
        start = self.PositionFromLine(line)
        end = self.GetLineEndPosition(line)
        self.SetSelection(start, end)

    def SetUpEditor(self):
        """
        This method carries out the work of setting up the demo editor.
        It's separate so as not to clutter up the init code.
        """
        import keyword

        self.SetLexer(stc.STC_LEX_PYTHON)
        self.SetKeyWords(0, " ".join(keyword.kwlist))

        # Enable folding
        self.SetProperty("fold", "1")

        # Highlight tab/space mixing (shouldn't be any)
        self.SetProperty("tab.timmy.whinge.level", "1")

        # Set left and right margins
        self.SetMargins(2, 2)

        # Set up the numbers in the margin for margin #1
        self.SetMarginType(1, stc.STC_MARGIN_NUMBER)
        # Reasonable value for, say, 4-5 digits using a mono font (40 pix)
        self.SetMarginWidth(1, 40)

        # Indentation and tab stuff
        self.SetIndent(4)  # Proscribed indent size for wx
        self.SetIndentationGuides(True)  # Show indent guides
        self.SetBackSpaceUnIndents(True)  # Backspace unindents rather than delete 1 space
        self.SetTabIndents(True)  # Tab key indents
        self.SetTabWidth(4)  # Proscribed tab size for wx
        self.SetUseTabs(False)  # Use spaces rather than tabs, or
        # TabTimmy will complain!
        # White space
        self.SetViewWhiteSpace(False)  # Don't view white space

        # EOL: Since we are loading/saving ourselves, and the
        # strings will always have \n's in them, set the STC to
        # edit them that way.
        self.SetEOLMode(stc.STC_EOL_LF)
        self.SetViewEOL(False)

        # No right-edge mode indicator
        self.SetEdgeMode(stc.STC_EDGE_NONE)

        # Setup a margin to hold fold markers
        self.SetMarginType(2, stc.STC_MARGIN_SYMBOL)
        self.SetMarginMask(2, stc.STC_MASK_FOLDERS)
        self.SetMarginSensitive(2, True)
        self.SetMarginWidth(2, 12)

        # and now set up the fold markers
        self.MarkerDefine(stc.STC_MARKNUM_FOLDEREND, stc.STC_MARK_BOXPLUSCONNECTED, "white", "black")
        self.MarkerDefine(stc.STC_MARKNUM_FOLDEROPENMID, stc.STC_MARK_BOXMINUSCONNECTED, "white", "black")
        self.MarkerDefine(stc.STC_MARKNUM_FOLDERMIDTAIL, stc.STC_MARK_TCORNER, "white", "black")
        self.MarkerDefine(stc.STC_MARKNUM_FOLDERTAIL, stc.STC_MARK_LCORNER, "white", "black")
        self.MarkerDefine(stc.STC_MARKNUM_FOLDERSUB, stc.STC_MARK_VLINE, "white", "black")
        self.MarkerDefine(stc.STC_MARKNUM_FOLDER, stc.STC_MARK_BOXPLUS, "white", "black")
        self.MarkerDefine(stc.STC_MARKNUM_FOLDEROPEN, stc.STC_MARK_BOXMINUS, "white", "black")

        # Global default style
        if wx.Platform == "__WXMSW__":
            self.StyleSetSpec(stc.STC_STYLE_DEFAULT, "fore:#000000,back:#FFFFFF,face:Courier New")
        elif wx.Platform == "__WXMAC__":
            # TODO: if this looks fine on Linux too, remove the Mac-specific case
            # and use this whenever OS != MSW.
            self.StyleSetSpec(stc.STC_STYLE_DEFAULT, "fore:#000000,back:#FFFFFF,face:Monaco")
        else:
            defsize = wx.SystemSettings.GetFont(wx.SYS_ANSI_FIXED_FONT).GetPointSize()
            self.StyleSetSpec(stc.STC_STYLE_DEFAULT, "fore:#000000,back:#FFFFFF,face:Courier,size:%d" % defsize)

        # Clear styles and revert to default.
        self.StyleClearAll()

        # Following style specs only indicate differences from default.
        # The rest remains unchanged.

        # Line numbers in margin
        self.StyleSetSpec(stc.STC_STYLE_LINENUMBER, "fore:#000000,back:#99A9C2")
        # Highlighted brace
        self.StyleSetSpec(stc.STC_STYLE_BRACELIGHT, "fore:#00009D,back:#FFFF00")
        # Unmatched brace
        self.StyleSetSpec(stc.STC_STYLE_BRACEBAD, "fore:#00009D,back:#FF0000")
        # Indentation guide
        self.StyleSetSpec(stc.STC_STYLE_INDENTGUIDE, "fore:#CDCDCD")

        # Python styles
        self.StyleSetSpec(stc.STC_P_DEFAULT, "fore:#000000")
        # Comments
        self.StyleSetSpec(stc.STC_P_COMMENTLINE, "fore:#008000,back:#F0FFF0")
        self.StyleSetSpec(stc.STC_P_COMMENTBLOCK, "fore:#008000,back:#F0FFF0")
        # Numbers
        self.StyleSetSpec(stc.STC_P_NUMBER, "fore:#008080")
        # Strings and characters
        self.StyleSetSpec(stc.STC_P_STRING, "fore:#800080")
        self.StyleSetSpec(stc.STC_P_CHARACTER, "fore:#800080")
        # Keywords
        self.StyleSetSpec(stc.STC_P_WORD, "fore:#000080,bold")
        # Triple quotes
        self.StyleSetSpec(stc.STC_P_TRIPLE, "fore:#800080,back:#FFFFEA")
        self.StyleSetSpec(stc.STC_P_TRIPLEDOUBLE, "fore:#800080,back:#FFFFEA")
        # Class names
        self.StyleSetSpec(stc.STC_P_CLASSNAME, "fore:#0000FF,bold")
        # Function names
        self.StyleSetSpec(stc.STC_P_DEFNAME, "fore:#008080,bold")
        # Operators
        self.StyleSetSpec(stc.STC_P_OPERATOR, "fore:#800000,bold")
        # Identifiers. I leave this as not bold because everything seems
        # to be an identifier if it doesn't match the above criterae
        self.StyleSetSpec(stc.STC_P_IDENTIFIER, "fore:#000000")

        # Caret color
        self.SetCaretForeground("BLUE")
        # Selection background
        self.SetSelBackground(1, "#66CCFF")

        # Attempt to set caret blink rate.
        try:
            self.SetCaretPeriod(GetCaretPeriod(self))
        except ValueError:
            pass

        self.SetSelBackground(True, wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHT))
        self.SetSelForeground(True, wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHTTEXT))

    def RegisterModifiedEvent(self, eventHandler):
        self.Bind(stc.EVT_STC_CHANGE, eventHandler)
