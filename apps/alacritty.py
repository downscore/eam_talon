"""Talon code for Alacritty support."""
# Disable linter warnings caused by Talon conventions.
# pylint: disable=no-self-argument, no-method-argument, relative-beyond-top-level
# pyright: reportSelfClsParameterName=false, reportGeneralTypeIssues=false
# mypy: ignore-errors

from talon import Context, Module

mod = Module()
ctx = Context()

mod.apps.alacritty = """
app.bundle: org.alacritty
"""

ctx.matches = r"""
app: alacritty
"""
