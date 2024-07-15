#!/usr/bin/env python
import py2exe
import shutil
import os
import customtkinter

if os.path.exists("dist"):
    shutil.rmtree("dist")

ctk_path = os.path.dirname(customtkinter.__file__)


def collect_ctk():
    data_files = []
    for root, folders, files in os.walk(ctk_path):
        relpath = os.path.relpath(root, ctk_path)
        for filename in files:
            ext = os.path.splitext(filename)
            if ext in [".ttf", ".json", ".png", ".otf"]:
                data_files.append(
                    (os.path.join(root, filename), os.path.join(relpath, filename))
                )
    return data_files


py2exe.freeze(
    version_info={
        "description": "CC2 Mission Editor",
        "version": "0.0.10",
    },
    windows=[{
        "dest_base": "cc2me",
        "script": "cc2me.py",
    }],
    data_files=collect_ctk(),
    options={
        "py2exe": {
            "packages": [
                "tkintermapview",
                "customtkinter",
            ],
            "excludes": [
                "unittest",
                "pdb",
                "doctest",
                "difflib",
            ],
        }
    }
)