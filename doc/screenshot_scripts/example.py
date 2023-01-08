import construct as cs

from doc.screenshot_scripts._helper import ScreenshotFrame


class Frame(ScreenshotFrame):
    screenshot_name = "example"

    def init_example(self):
        # show construct
        constr = cs.Struct(
            "signature" / cs.Const(b"BMP"),
            "width" / cs.Int8ub,
            "height" / cs.Int8ub,
            "pixels" / cs.Array(cs.this.width * cs.this.height, cs.Byte),
        )
        b = b"BMP\x03\x02\x07\x08\t\x0b\x0c\r"

        self.editor_panel.change_construct(constr)
        self.editor_panel.change_binary(b)
        self.editor_panel.construct_editor.expand_all()


if __name__ == "__main__":
    Frame.create_screenshot(auto_close=False)
