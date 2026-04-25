# Theme Hub Product Spec

## Purpose

Hermes Theme Hub is a dashboard plugin for discovering installed Hermes
dashboard themes and theme-capable plugin packages.

It gives users one local dashboard surface for:

- seeing the active dashboard theme
- seeing installed user themes
- discovering theme files shipped by plugins
- installing a selected plugin theme into the active Hermes home
- activating installed or built-in themes

## Theme Plugin Contract

A theme plugin is a portable Hermes user plugin folder with:

```text
plugin.yaml
theme/*.yaml
```

The hub discovers theme plugins from normal Hermes plugin locations and displays
safe user-facing paths such as:

```text
~/.hermes/plugins/<plugin-name>
```

## Boundaries

- Theme Hub does not modify Hermes core files.
- Theme Hub does not publish themes to GitHub.
- Theme Hub does not claim official Hermes certification.
- Theme installation copies only selected `theme/*.yaml` files into the active
  Hermes home.
- Local dashboard URLs are loopback-only and should use `HERMES_DASHBOARD_URL`
  when the dashboard is running on a non-default local port.
