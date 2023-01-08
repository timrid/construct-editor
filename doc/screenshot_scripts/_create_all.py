import importlib


def create_all():
    screenshot_module_names = [
        "doc.screenshot_scripts.bitwise",
        "doc.screenshot_scripts.example",
    ]

    for module_name in screenshot_module_names:
        module = importlib.import_module(module_name)
        module.Frame.create_screenshot()


if __name__ == "__main__":
    create_all()
