import construct as cs

from doc.screenshot_scripts._helper import ScreenshotFrame



class Frame(ScreenshotFrame):
    screenshot_name = "bitwise"

    def init_example(self):
        # show construct
        constr = cs.Bitwise(cs.GreedyRange(cs.Bit))
        b = bytes([0x12])

        self.editor_panel.change_construct(constr)
        self.editor_panel.change_binary(b)
        self.editor_panel.construct_editor.expand_all()

        # select item
        editor = self.editor_panel.construct_editor
        model = editor.get_model()

        childs = model.get_children(None)
        childs = model.get_children(childs[0])
        editor.select_entry(childs[1])


if __name__ == "__main__":
    Frame.create_screenshot(auto_close=False)
