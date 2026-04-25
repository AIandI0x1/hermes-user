"""Hermes dashboard Plugins sidebar integration.

The dashboard extension itself is declared in dashboard/manifest.json.
This module makes the bundle visible to Hermes' general plugin manager so
the same plugin can be enabled, disabled, and listed by the normal plugin
workflow without patching Hermes core.
"""


def register(ctx):
    """Register no runtime hooks; this plugin contributes dashboard assets."""

    return None
