(function () {
  "use strict";

  const SDK = window.__HERMES_PLUGIN_SDK__;
  const { React } = SDK;
  const { useEffect, useState } = SDK.hooks;
  const { Badge, Button, Card, CardContent, CardHeader, CardTitle, Separator } = SDK.components;

  function h(type, props) {
    const children = Array.prototype.slice.call(arguments, 2);
    return React.createElement.apply(React, [type, props].concat(children));
  }

  function ThemeRow(props) {
    const theme = props.theme;
    const active = props.active === theme.name;
    return h("div", { className: "hth-theme-row" },
      h("div", { className: "hth-theme-main" },
        h("strong", null, theme.label || theme.name),
        h("span", null, theme.name),
        theme.description ? h("p", null, theme.description) : null,
        h("div", { className: "hth-chip-row" },
          h("span", { className: "hth-chip" }, theme.source),
          h("span", { className: "hth-chip" }, theme.layout_variant || "standard"),
          theme.has_custom_css ? h("span", { className: "hth-chip hth-chip-accent" }, "custom css") : null,
          active ? h("span", { className: "hth-chip hth-chip-active" }, "active") : null,
        ),
      ),
      h("div", { className: "hth-theme-actions" },
        !theme.installed && theme.plugin ? h(Button, {
          variant: "outline",
          onClick: function () { props.onInstall(theme); },
          disabled: props.busy,
        }, "Install") : null,
        theme.installed || theme.source === "installed" ? h(Button, {
          variant: active ? "secondary" : "outline",
          onClick: function () { props.onActivate(theme.name); },
          disabled: props.busy || active,
        }, active ? "Active" : "Activate") : null,
      ),
    );
  }

  function ThemeHubPage() {
    const [inventory, setInventory] = useState(null);
    const [loading, setLoading] = useState(true);
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState("");

    function load() {
      setLoading(true);
      setError("");
      SDK.fetchJSON("/api/plugins/hermes-theme-hub/themes")
        .then(function (data) { setInventory(data); })
        .catch(function (err) { setError(err && err.message ? err.message : "Unable to load themes."); })
        .finally(function () { setLoading(false); });
    }

    function activate(name) {
      setBusy(true);
      setError("");
      SDK.fetchJSON("/api/plugins/hermes-theme-hub/activate", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: name }),
      })
        .then(function (result) {
          if (result && result.ok === false) throw new Error(result.error || "Unable to activate theme.");
          load();
        })
        .catch(function (err) { setError(err && err.message ? err.message : "Unable to activate theme."); })
        .finally(function () { setBusy(false); });
    }

    function install(theme) {
      setBusy(true);
      setError("");
      SDK.fetchJSON("/api/plugins/hermes-theme-hub/install", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ plugin: theme.plugin, theme: theme.name }),
      })
        .then(function (result) {
          if (result && result.ok === false) throw new Error(result.error || "Unable to install theme.");
          load();
        })
        .catch(function (err) { setError(err && err.message ? err.message : "Unable to install theme."); })
        .finally(function () { setBusy(false); });
    }

    useEffect(function () { load(); }, []);

    const installed = inventory && Array.isArray(inventory.installed) ? inventory.installed : [];
    const themePlugins = inventory && Array.isArray(inventory.theme_plugins) ? inventory.theme_plugins : [];
    const providedThemes = [];
    themePlugins.forEach(function (plugin) {
      (plugin.themes || []).forEach(function (theme) {
        providedThemes.push(Object.assign({}, theme, { plugin: plugin.name, pluginPath: plugin.path }));
      });
    });

    return h("div", { className: "hth-page" },
      h("div", { className: "hth-title-row" },
        h("div", null,
          h("h1", { className: "hth-page-title" }, "Theme Hub"),
          h("p", { className: "hth-muted" }, "Discover installed dashboard themes and theme plugins."),
        ),
        inventory ? h(Badge, { variant: "outline" }, "Active: " + inventory.active) : null,
      ),
      error ? h("p", { className: "hth-error" }, error) : null,
      loading ? h("p", { className: "hth-muted" }, "Loading themes...") : null,

      h("div", { className: "hth-grid" },
        h(Card, null,
          h(CardHeader, null, h(CardTitle, null, "Installed Themes")),
          h(CardContent, null,
            installed.length ? h("div", { className: "hth-stack" },
              ...installed.map(function (theme) {
                return h(ThemeRow, {
                  key: "installed-" + theme.name,
                  theme: theme,
                  active: inventory && inventory.active,
                  onActivate: activate,
                  onInstall: install,
                  busy: busy,
                });
              }),
            ) : h("p", { className: "hth-muted" }, "No user themes installed yet. Built-in themes are available from the dashboard theme switcher."),
          ),
        ),
        h(Card, null,
          h(CardHeader, null, h(CardTitle, null, "Theme Plugins")),
          h(CardContent, null,
            providedThemes.length ? h("div", { className: "hth-stack" },
              ...providedThemes.map(function (theme) {
                return h(ThemeRow, {
                  key: theme.plugin + "-" + theme.name,
                  theme: theme,
                  active: inventory && inventory.active,
                  onActivate: activate,
                  onInstall: install,
                  busy: busy,
                });
              }),
            ) : h("p", { className: "hth-muted" }, "No theme plugin packages found. Add a plugin with theme/*.yaml to make it appear here."),
          ),
        ),
      ),
      h(Card, null,
        h(CardHeader, null, h(CardTitle, null, "Theme Plugin Contract")),
        h(CardContent, null,
          h("p", { className: "hth-muted" }, "A theme plugin is a portable user plugin folder with plugin.yaml plus one or more theme/*.yaml files. The hub discovers those packages automatically from Hermes plugin locations."),
          h(Separator, null),
          h("code", { className: "hth-code" }, "~/.hermes/plugins/<plugin-name>/theme/<theme-name>.yaml"),
        ),
      ),
    );
  }

  window.__HERMES_PLUGINS__.register("hermes-theme-hub", ThemeHubPage);
})();
