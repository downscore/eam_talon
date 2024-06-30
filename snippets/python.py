"""Support for snippets."""
# Disable linter warnings caused by Talon conventions.
# pylint: disable=no-self-argument, no-method-argument, relative-beyond-top-level
# pyright: reportSelfClsParameterName=false, reportGeneralTypeIssues=false
# mypy: ignore-errors

from talon import Context, Module
from ..core.snippets import load_snippets_json

mod = Module()
ctx = Context()

mod.list("snippet_python", desc="Common Python snippets")
ctx.lists["user.snippet_python"] = load_snippets_json("python.json")
