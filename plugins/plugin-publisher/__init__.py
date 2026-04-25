"""Hermes plugin publisher user plugin."""

from __future__ import annotations

from pathlib import Path

try:
    from .tools.publisher import HERMES_PLUGIN_PUBLISH_PLAN_SCHEMA, publish_plan
except ImportError:
    from tools.publisher import HERMES_PLUGIN_PUBLISH_PLAN_SCHEMA, publish_plan


PLUGIN_ROOT = Path(__file__).resolve().parent


def register(ctx):
    """Register the plugin publishing tool and its operator skill."""

    ctx.register_skill(
        name="plugin-publisher",
        path=PLUGIN_ROOT / "skills" / "plugin-publisher" / "SKILL.md",
        description=(
            "Audit a Hermes plugin folder and prepare safe GitHub publishing "
            "steps with a redacted secret-risk scan."
        ),
    )
    ctx.register_tool(
        name="hermes_plugin_publish_plan",
        toolset="development",
        schema=HERMES_PLUGIN_PUBLISH_PLAN_SCHEMA,
        handler=publish_plan,
        emoji="🚀",
    )
