#!/usr/bin/env python
from setuptools import setup

exec(open("./construct_editor/version.py").read())

setup(
    name="construct-editor",
    version=version_string,  # type: ignore
    packages=[
        "construct_editor",
        "construct_editor.gallery",
        "construct_editor.helper",
        "construct_editor.widgets",
    ],
    package_data={
        "construct_editor": ["py.typed"],
    },
    entry_points={
        "gui_scripts": [
            "construct-editor=construct_editor.main:main"
        ]
    },
    include_package_data=True,
    license="MIT",
    description="GUI (based on wxPython) for 'construct', which is a powerful declarative and symmetrical parser and builder for binary data.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    platforms=["Windows"],
    url="https://github.com/timrid/construct-editor",
    author="Tim Riddermann",
    python_requires="==3.8.*",
    install_requires=[
        "construct==2.10.67",
        "construct-typing==0.5.1",
        "wxPython>=4.1.1",
        "arrow>=1.0.0"
    ],
    keywords=[
        "gui",
        "wx",
        "wxpython",
        "widget",
        "binary",
        "editor" "construct",
        "kaitai",
        "declarative",
        "data structure",
        "struct",
        "binary",
        "symmetric",
        "parser",
        "builder",
        "parsing",
        "building",
        "pack",
        "unpack",
        "packer",
        "unpacker",
        "bitstring",
        "bytestring",
        "bitstruct",
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: Implementation :: CPython",
        "Typing :: Typed",
    ],
)
