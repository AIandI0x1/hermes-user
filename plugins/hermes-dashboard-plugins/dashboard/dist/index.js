(function () {
  "use strict";

  const SDK = window.__HERMES_PLUGIN_SDK__;
  const { React } = SDK;
  const { useEffect, useMemo, useState } = SDK.hooks;
  const {
    Badge,
    Button,
    Card,
    CardContent,
    CardHeader,
    CardTitle,
    Separator,
  } = SDK.components;
  const MANAGER_PLUGIN_NAME = "hermes-dashboard-plugins";
  const MANAGER_ICON_URL = "/dashboard-plugins/hermes-dashboard-plugins/assets/plugin-cubes.svg";
  let dashboardVisibilityObserver = null;
  let dashboardVisibilityTimer = null;
  let latestDashboardPlugins = [];
  let latestDisabledPlugins = new Set();

  function statusLabel(plugin) {
    if (!plugin) return "No plugin selected";
    if (!plugin.ok) return "Needs fixes";
    if (plugin.warnings && plugin.warnings.length) return "Ready with warnings";
    return "Ready";
  }

  function statusClass(plugin) {
    if (!plugin) return "hhh-status-warn";
    if (!plugin.ok) return "hhh-status-error";
    if (plugin.warnings && plugin.warnings.length) return "hhh-status-warn";
    return "hhh-status-ok";
  }

  function trustLabel(trust) {
    if (!trust) return "Unsigned";
    if (trust.status === "locally_validated") return "Locally Validated";
    if (trust.status === "hermes_certified") return "Hermes Certified";
    return "Unsigned";
  }

  function originLabel(origin, fallback) {
    if (origin && origin.label) return origin.label;
    if (fallback === "bundled") return "Upstream";
    if (fallback === "user") return "User";
    return "Third Party";
  }

  function originClass(origin, fallback) {
    const type = origin && origin.type ? origin.type : (fallback === "bundled" ? "upstream" : fallback || "third_party");
    if (type === "upstream") return "hhh-chip-upstream";
    if (type === "third_party") return "hhh-chip-third-party";
    return "hhh-chip-user";
  }

  function h(type, props) {
    const children = Array.prototype.slice.call(arguments, 2);
    return React.createElement.apply(React, [type, props].concat(children));
  }

  function pluginRoute(manifest) {
    return manifest && manifest.tab && manifest.tab.path ? manifest.tab.path : "";
  }

  function routeMatches(anchor, route) {
    const href = anchor.getAttribute("href");
    if (!href) return false;
    if (href === route) return true;
    try {
      return new URL(href, window.location.origin).pathname === route;
    } catch (err) {
      return false;
    }
  }

  function managerIconElement(className) {
    return h("span", {
      className: className || "hhh-cubes-icon",
      "aria-hidden": "true",
      style: { WebkitMaskImage: "url(" + MANAGER_ICON_URL + ")", maskImage: "url(" + MANAGER_ICON_URL + ")" },
    });
  }

  function applyManagerSidebarIcon() {
    document.querySelectorAll("a[href]").forEach(function (anchor) {
      if (!routeMatches(anchor, "/plugins")) return;
      if (anchor.getAttribute("data-hhh-manager-icon") === "true") return;
      const existing = anchor.querySelector("svg");
      if (!existing) return;
      const icon = document.createElement("span");
      icon.className = existing.getAttribute("class") || "h-3.5 w-3.5 shrink-0";
      icon.classList.add("hhh-sidebar-cubes-icon");
      icon.setAttribute("aria-hidden", "true");
      icon.style.webkitMaskImage = "url(" + MANAGER_ICON_URL + ")";
      icon.style.maskImage = "url(" + MANAGER_ICON_URL + ")";
      existing.replaceWith(icon);
      anchor.setAttribute("data-hhh-manager-icon", "true");
    });
  }

  function setRouteVisible(manifest, visible) {
    const route = pluginRoute(manifest);
    if (!route) return;

    document.querySelectorAll("[data-hhh-hidden-plugin='" + manifest.name + "']").forEach(function (node) {
      node.style.display = "";
      node.removeAttribute("data-hhh-hidden-plugin");
    });

    if (visible) return;

    document.querySelectorAll("a[href]").forEach(function (anchor) {
      if (!routeMatches(anchor, route)) return;
      const container = anchor.closest("li") || anchor;
      container.style.display = "none";
      container.setAttribute("data-hhh-hidden-plugin", manifest.name);
    });
  }

  function applyDashboardVisibility(manifests, disabled) {
    latestDashboardPlugins = Array.isArray(manifests) ? manifests : latestDashboardPlugins;
    latestDisabledPlugins = disabled instanceof Set ? disabled : latestDisabledPlugins;
    applyManagerSidebarIcon();

    latestDashboardPlugins.forEach(function (manifest) {
      if (!manifest || !manifest.name) return;
      if (manifest.name === MANAGER_PLUGIN_NAME) {
        setRouteVisible(manifest, true);
        return;
      }
      setRouteVisible(manifest, !latestDisabledPlugins.has(manifest.name));
    });

    const current = window.location.pathname;
    const blocked = latestDashboardPlugins.find(function (manifest) {
      return manifest && manifest.name !== MANAGER_PLUGIN_NAME
        && latestDisabledPlugins.has(manifest.name)
        && pluginRoute(manifest) === current;
    });
    if (blocked) window.location.assign("/plugins");
  }

  function refreshDashboardVisibility() {
    return Promise.all([
      SDK.fetchJSON("/api/dashboard/plugins"),
      SDK.fetchJSON("/api/plugins/hermes-dashboard-plugins/state"),
    ]).then(function (results) {
      const disabled = new Set(Array.isArray(results[1] && results[1].disabled) ? results[1].disabled : []);
      applyDashboardVisibility(Array.isArray(results[0]) ? results[0] : [], disabled);
      return results;
    });
  }

  function startDashboardVisibilityController() {
    refreshDashboardVisibility().catch(function () {});
    if (!dashboardVisibilityObserver && window.MutationObserver) {
      dashboardVisibilityObserver = new MutationObserver(function () {
        applyDashboardVisibility();
      });
      dashboardVisibilityObserver.observe(document.body, { childList: true, subtree: true });
    }
    if (!dashboardVisibilityTimer) {
      dashboardVisibilityTimer = window.setInterval(function () {
        applyDashboardVisibility();
      }, 1500);
    }
  }

  function IssueList(props) {
    if (!props.items || props.items.length === 0) {
      return h("p", { className: "hhh-muted" }, props.empty);
    }
    return h("ul", { className: "hhh-issues" },
      ...props.items.map(function (item) {
        return h("li", { key: item }, item);
      }),
    );
  }

  function PluginCard(props) {
    const plugin = props.plugin;
    const manifest = plugin.manifest || {};
    const selected = props.selected;
    const route = plugin.route || "no dashboard";
    const ownPlugin = manifest.name === "hermes-hackathon-hub";
    const protectedPlugin = manifest.name === MANAGER_PLUGIN_NAME;
    return h("div", {
      className: "hhh-plugin-card" + (selected ? " hhh-plugin-card-selected" : ""),
      "data-plugin-name": manifest.name || plugin.id || "",
      role: "button",
      tabIndex: 0,
      onClick: function () { props.onSelect(plugin); },
      onKeyDown: function (event) {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          props.onSelect(plugin);
        }
      },
    },
        h("div", { className: "hhh-plugin-card-head" },
        h("div", { className: "hhh-plugin-icon" },
          protectedPlugin ? managerIconElement("hhh-cubes-icon hhh-card-cubes-icon") : (manifest.icon || "P").slice(0, 1),
        ),
        h("div", { className: "hhh-plugin-card-title" },
          h("strong", null, manifest.label || manifest.name || "Untitled plugin"),
          h("span", null, manifest.name || "unknown-plugin"),
        ),
        h("button", {
          className: "hhh-switch" + (plugin.enabled ? " hhh-switch-on" : ""),
          type: "button",
          role: "switch",
          "aria-checked": Boolean(plugin.enabled),
          title: protectedPlugin ? "The dashboard plugin manager stays enabled so plugins can be re-enabled." : undefined,
          disabled: props.toggling || protectedPlugin,
          onClick: function (event) {
            event.stopPropagation();
            props.onToggle(plugin);
          },
        },
          h("span", { className: "hhh-switch-thumb" }),
        ),
      ),
      h("p", { className: "hhh-plugin-description" }, manifest.description || "No description provided."),
      h("div", { className: "hhh-chip-row" },
        ownPlugin ? h("span", { className: "hhh-chip hhh-chip-primary" }, "hackathon hub") : null,
        plugin.hasDashboard ? h("span", { className: "hhh-chip hhh-chip-primary" }, "dashboard") : h("span", { className: "hhh-chip" }, "runtime"),
        h("span", { className: "hhh-chip " + originClass(plugin.origin, plugin.source) }, originLabel(plugin.origin, plugin.source)),
        h("span", { className: "hhh-chip" }, route),
        h("span", { className: "hhh-chip " + statusClass(plugin) }, statusLabel(plugin)),
        h("span", { className: "hhh-chip" }, protectedPlugin ? "manager" : (plugin.enabled ? "enabled" : "disabled")),
      ),
    );
  }

  function HackathonHubPage() {
    const [plugins, setPlugins] = useState([]);
    const [selectedPath, setSelectedPath] = useState("");
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
    const [toggling, setToggling] = useState({});

    function loadPlugins() {
      setLoading(true);
      setError("");
      Promise.all([
        SDK.fetchJSON("/api/plugins/hermes-dashboard-plugins/catalog"),
        SDK.fetchJSON("/api/plugins/hermes-dashboard-plugins/state"),
      ])
        .then(function (results) {
          const data = results[0] && Array.isArray(results[0].plugins) ? results[0].plugins : [];
          const state = results[1] || {};
          const disabled = new Set(Array.isArray(state.disabled) ? state.disabled : []);
          const dashboardManifests = data.filter(function (plugin) { return plugin.has_dashboard; }).map(function (plugin) {
            return {
              name: plugin.name,
              tab: plugin.route ? { path: plugin.route } : {},
            };
          });
          applyDashboardVisibility(dashboardManifests, disabled);
          const list = Array.isArray(data) ? data.map(function (plugin) {
            const manifest = {
              name: plugin.name,
              label: plugin.label,
              description: plugin.description,
              icon: plugin.icon,
              version: plugin.version,
              entry: plugin.entry,
              tab: plugin.route ? { path: plugin.route } : {},
            };
            return {
              id: plugin.name,
              source: plugin.source || "unknown",
              origin: plugin.origin || null,
              enabled: Boolean(plugin.enabled),
              ok: !(plugin.errors && plugin.errors.length),
              errors: plugin.errors || [],
              warnings: plugin.warnings || [],
              hasDashboard: Boolean(plugin.has_dashboard),
              route: plugin.route || "",
              kind: plugin.kind || "standalone",
              providesTools: plugin.provides_tools || [],
              providesHooks: plugin.provides_hooks || [],
              manifest: manifest,
              trust: plugin.trust || {
                status: "locally_validated",
                official_verification: "unavailable",
                detail: "Discovered by the Hermes plugin manager."
              },
            };
          }) : [];
          setPlugins(list);
        })
        .catch(function (err) {
          setError(err && err.message ? err.message : "Unable to scan plugins.");
        })
        .finally(function () {
          setLoading(false);
        });
    }

    useEffect(function () {
      startDashboardVisibilityController();
      loadPlugins();
    }, []);

    const selected = useMemo(function () {
      return plugins.find(function (plugin) { return plugin.id === selectedPath; }) || null;
    }, [plugins, selectedPath]);

    const manifest = selected && selected.manifest ? selected.manifest : {};

    function openPlugin(plugin) {
      setSelectedPath(plugin.id);
    }

    function togglePlugin(plugin) {
      const nextEnabled = !plugin.enabled;
      if (plugin.id === MANAGER_PLUGIN_NAME && !nextEnabled) {
        setError("The dashboard plugin manager must stay enabled so plugins can be re-enabled.");
        return;
      }
      setToggling(function (current) {
        const next = Object.assign({}, current);
        next[plugin.id] = true;
        return next;
      });
      SDK.fetchJSON("/api/plugins/hermes-dashboard-plugins/toggle", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: plugin.id, enabled: nextEnabled }),
      })
        .then(function (result) {
          if (result && result.ok === false) {
            throw new Error(result.error || "Unable to toggle plugin.");
          }
          setPlugins(function (current) {
            return current.map(function (item) {
              return item.id === plugin.id ? Object.assign({}, item, { enabled: nextEnabled }) : item;
            });
          });
          return refreshDashboardVisibility();
        })
        .catch(function (err) {
          setError(err && err.message ? err.message : "Unable to toggle plugin.");
        })
        .finally(function () {
          setToggling(function (current) {
            const next = Object.assign({}, current);
            delete next[plugin.id];
            return next;
          });
        });
    }

    return h("div", { className: "hhh-page" },
      h("div", { className: "hhh-title-row" },
        h("div", null,
          h("h1", { className: "hhh-page-title" }, "Plugins"),
          h("p", { className: "hhh-muted" }, "User and bundled Hermes plugins"),
        ),
      ),
      error ? h("p", { className: "hhh-error" }, error) : null,

      plugins.length
        ? h("div", { className: "hhh-plugin-cards" },
            ...plugins.map(function (plugin) {
              return h(PluginCard, {
                key: plugin.id,
                plugin: plugin,
                selected: selected && selected.id === plugin.id,
                onSelect: openPlugin,
                onToggle: togglePlugin,
                toggling: Boolean(toggling[plugin.id]),
              });
            }),
          )
        : h("p", { className: "hhh-muted" }, loading ? "Loading plugins..." : "No dashboard plugins found."),

      selected ? h("div", { className: "hhh-grid hhh-grid-wide" },

        h(Card, null,
          h(CardHeader, null,
            h("div", { className: "hhh-title-row" },
              h(CardTitle, null, manifest.label || manifest.name || "Plugin Details"),
              h(Badge, { variant: "outline" }, selected.source || "unknown"),
              h(Badge, { variant: "outline" }, statusLabel(selected)),
            ),
          ),
          h(CardContent, null,
            selected ? h("div", { className: "hhh-stack" },
              h("div", null,
                h("strong", null, manifest.name || "Unknown plugin"),
                h("p", { className: "hhh-muted" }, manifest.description || "No description provided."),
              ),
              h(Separator, null),
              h("div", { className: "hhh-detail-grid" },
                h("div", null, h("span", { className: "hhh-detail-label" }, "Label"), h("strong", null, manifest.label || "-")),
                h("div", null, h("span", { className: "hhh-detail-label" }, "Origin"), h("strong", null, originLabel(selected.origin, selected.source))),
                h("div", null, h("span", { className: "hhh-detail-label" }, "Source"), h("strong", null, selected.source || "-")),
                h("div", null, h("span", { className: "hhh-detail-label" }, "Version"), h("strong", null, manifest.version || "-")),
                h("div", null, h("span", { className: "hhh-detail-label" }, "Kind"), h("strong", null, selected.kind || "-")),
                h("div", null, h("span", { className: "hhh-detail-label" }, "Route"), h("strong", null, manifest.tab && manifest.tab.path ? manifest.tab.path : "no dashboard")),
                h("div", null, h("span", { className: "hhh-detail-label" }, "Tools"), h("strong", null, selected.providesTools && selected.providesTools.length ? selected.providesTools.join(", ") : "-")),
                h("div", null, h("span", { className: "hhh-detail-label" }, "Entry"), h("strong", null, manifest.entry || "-")),
              ),
              h(Separator, null),
              selected.origin && selected.origin.detail ? h("div", { className: "hhh-trust" },
                h("strong", null, "Origin: " + originLabel(selected.origin, selected.source)),
                h("p", { className: "hhh-muted" }, selected.origin.detail),
              ) : null,
              selected.origin && selected.origin.detail ? h(Separator, null) : null,
              h("div", null,
                h("h3", { className: "hhh-section-title hhh-status-error" }, "Errors"),
                h(IssueList, { items: selected.errors || [], empty: "No blocking errors." }),
              ),
              h("div", null,
                h("h3", { className: "hhh-section-title hhh-status-warn" }, "Warnings"),
                h(IssueList, { items: selected.warnings || [], empty: "No publish-readiness warnings." }),
              ),
              h("div", { className: "hhh-trust" },
                h("strong", null, "Trust: " + trustLabel(selected.trust)),
                h("p", { className: "hhh-muted" }, selected.trust ? selected.trust.detail : "No trust metadata available."),
                h("p", { className: "hhh-muted" }, "Official verification: " + ((selected.trust && selected.trust.official_verification) || "unavailable")),
                h("p", { className: "hhh-muted" }, "Future certified status requires an official Hermes registry entry and public signing key."),
              ),
            ) : h("p", { className: "hhh-muted" }, "Select a plugin to inspect."),
          ),
        ),
      ) : null,
    );
  }

  startDashboardVisibilityController();
  window.__HERMES_PLUGINS__.register("hermes-dashboard-plugins", HackathonHubPage);
})();
