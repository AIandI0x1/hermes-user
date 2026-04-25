(function () {
  "use strict";

  const SDK = window.__HERMES_PLUGIN_SDK__;
  const { React } = SDK;

  const PUBLISHER_NAME = "hermes-plugin-publisher";
  const BUTTON_CLASS = "hpp-publish-button";
  const MODAL_ID = "hpp-publish-modal";
  let observer = null;
  let enabled = false;
  let catalog = [];

  function h(type, props) {
    const children = Array.prototype.slice.call(arguments, 2);
    return React.createElement.apply(React, [type, props].concat(children));
  }

  function UploadIcon() {
    return h("svg", {
      viewBox: "0 0 24 24",
      fill: "none",
      stroke: "currentColor",
      strokeWidth: 2,
      strokeLinecap: "round",
      strokeLinejoin: "round",
      "aria-hidden": "true",
    },
      h("path", { d: "M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" }),
      h("path", { d: "M17 8l-5-5-5 5" }),
      h("path", { d: "M12 3v12" }),
    );
  }

  function applyPublisherSidebarIcon() {
    document.querySelectorAll("[data-hpp-hidden-route='true']").forEach(function (node) {
      if (enabled) {
        node.style.display = "";
        node.removeAttribute("data-hpp-hidden-route");
      }
    });
    document.querySelectorAll("[data-hhh-hidden-plugin='" + PUBLISHER_NAME + "']").forEach(function (node) {
      if (enabled) {
        node.style.display = "";
        node.removeAttribute("data-hhh-hidden-plugin");
      }
    });

    if (!enabled) {
      document.querySelectorAll("a[href]").forEach(function (anchor) {
        if (!routeMatches(anchor, "/plugin-publisher")) return;
        const container = anchor.closest("li") || anchor;
        container.style.display = "none";
        container.setAttribute("data-hpp-hidden-route", "true");
      });
      if (window.location.pathname === "/plugin-publisher") window.location.assign("/plugins");
      return;
    }

    document.querySelectorAll("a[href]").forEach(function (anchor) {
      if (!routeMatches(anchor, "/plugin-publisher")) return;
      const container = anchor.closest("li") || anchor;
      container.style.display = "";
      container.removeAttribute("data-hpp-hidden-route");
      container.removeAttribute("data-hhh-hidden-plugin");
      if (anchor.getAttribute("data-hpp-icon") === "true") return;
      const existing = anchor.querySelector("svg");
      if (!existing) return;
      const icon = document.createElement("span");
      icon.className = existing.getAttribute("class") || "h-3.5 w-3.5 shrink-0";
      icon.classList.add("hpp-sidebar-upload-icon");
      icon.setAttribute("aria-hidden", "true");
      icon.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="M17 8l-5-5-5 5"/><path d="M12 3v12"/></svg>';
      existing.replaceWith(icon);
      anchor.setAttribute("data-hpp-icon", "true");
    });
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

  function isPublisherEnabled(state) {
    const disabled = new Set(Array.isArray(state && state.disabled) ? state.disabled : []);
    const enabledList = new Set(Array.isArray(state && state.enabled) ? state.enabled : []);
    return enabledList.has(PUBLISHER_NAME) && !disabled.has(PUBLISHER_NAME);
  }

  function loadState() {
    return Promise.all([
      SDK.fetchJSON("/api/plugins/hermes-dashboard-plugins/state"),
      SDK.fetchJSON("/api/plugins/hermes-dashboard-plugins/catalog").catch(function () { return { plugins: [] }; }),
    ]).then(function (results) {
      enabled = isPublisherEnabled(results[0] || {});
      catalog = Array.isArray(results[1] && results[1].plugins) ? results[1].plugins : [];
      applyPublisherSidebarIcon();
      applyButtons();
    }).catch(function () {
      enabled = false;
    });
  }

  function pluginFromCard(card) {
    const cardName = (card.getAttribute("data-plugin-name") || "").trim();
    if (cardName) {
      return catalog.find(function (item) { return item.name === cardName; }) || { name: cardName, label: cardName };
    }
    const title = card.querySelector(".hhh-plugin-card-title strong");
    if (!title) return null;
    const name = (title.textContent || "").trim();
    return catalog.find(function (item) { return item.name === name; }) || { name: name, label: name };
  }

  function applyButtons() {
    if (!enabled) {
      document.querySelectorAll("." + BUTTON_CLASS).forEach(function (button) {
        button.remove();
      });
      return;
    }
    if (!enabled || window.location.pathname !== "/plugins") return;
    document.querySelectorAll(".hhh-plugin-card").forEach(function (card) {
      if (card.querySelector("." + BUTTON_CLASS)) return;
      const plugin = pluginFromCard(card);
      if (!plugin || !plugin.name) return;
      const head = card.querySelector(".hhh-plugin-card-head");
      if (!head) return;
      const button = document.createElement("button");
      button.type = "button";
      button.className = BUTTON_CLASS;
      button.title = "Publish plugin to GitHub";
      button.setAttribute("aria-label", "Publish " + plugin.name + " to GitHub");
      button.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="M17 8l-5-5-5 5"/><path d="M12 3v12"/></svg>';
      button.addEventListener("click", function (event) {
        event.preventDefault();
        event.stopPropagation();
        openPublishModal(plugin);
      });
      const switchButton = head.querySelector("button[role='switch']");
      if (switchButton) {
        head.insertBefore(button, switchButton);
      } else {
        head.appendChild(button);
      }
    });
  }

  function removeModal() {
    const existing = document.getElementById(MODAL_ID);
    if (existing) existing.remove();
  }

  function defaultRepoPath(plugin) {
    return plugin.repo_path || plugin.name || "";
  }

  function loadDefaults(pluginName) {
    if (!pluginName) return Promise.resolve({ repoPath: "", githubPath: "" });
    return SDK.fetchJSON("/api/plugins/hermes-plugin-publisher/defaults", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ plugin_name: pluginName }),
    }).then(function (data) {
      return {
        repoPath: data && data.ok && data.repo_path ? data.repo_path : pluginName,
        githubPath: data && data.ok && data.github_path && data.github_path.path ? data.github_path.path : "",
      };
    }).catch(function () {
      return { repoPath: pluginName, githubPath: "" };
    });
  }

  function loadReadme(pluginName) {
    if (!pluginName) return Promise.resolve({ hasReadme: false, content: "" });
    return SDK.fetchJSON("/api/plugins/hermes-plugin-publisher/readme", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ plugin_name: pluginName }),
    }).then(function (data) {
      return {
        hasReadme: Boolean(data && data.ok && data.has_readme),
        content: data && data.ok && data.content ? data.content : "",
        truncated: Boolean(data && data.truncated),
      };
    }).catch(function () {
      return { hasReadme: false, content: "" };
    });
  }

  function openPublishModal(plugin) {
    removeModal();
    const initialRepoPath = defaultRepoPath(plugin);
    const overlay = document.createElement("div");
    overlay.id = MODAL_ID;
    overlay.className = "hpp-modal-overlay";
    overlay.innerHTML = [
      '<div class="hpp-modal" role="dialog" aria-modal="true" aria-label="Publish plugin">',
      '<div class="hpp-modal-head">',
      '<strong>Publish ' + escapeHtml(plugin.name) + '</strong>',
      '<button type="button" class="hpp-close" aria-label="Close">×</button>',
      '</div>',
      '<label class="hpp-field">Publish destination path<input class="hpp-input" value="' + escapeHtml(initialRepoPath) + '" placeholder="owner/repo/path"></label>',
      '<div class="hpp-path-note">Catalog reference path: <strong class="hpp-github-path">checking...</strong></div>',
      '<label class="hpp-field">Visibility<select class="hpp-input"><option value="public">public</option><option value="private">private</option></select></label>',
      '<div class="hpp-result hpp-muted">Confirm publish uses the destination repo above. If that repo does not exist, publisher creates it first; if it exists, publisher pushes without changing visibility.</div>',
      '<div class="hpp-actions">',
      '<button type="button" class="hpp-confirm">Confirm publish</button>',
      '<button type="button" class="hpp-cancel">Cancel</button>',
      '</div>',
      '</div>',
    ].join("");
    document.body.appendChild(overlay);
    loadDefaults(plugin.name).then(function (defaults) {
      const input = overlay.querySelector("input");
      const path = overlay.querySelector(".hpp-github-path");
      if (input && (!input.value || input.value === plugin.name)) input.value = defaults.repoPath;
      if (path) path.textContent = defaults.githubPath || "unavailable";
    });
    overlay.querySelector(".hpp-close").addEventListener("click", removeModal);
    overlay.querySelector(".hpp-cancel").addEventListener("click", removeModal);
    overlay.querySelector(".hpp-confirm").addEventListener("click", function () {
      publishPlugin(plugin, overlay);
    });
  }

  function escapeHtml(text) {
    return String(text || "").replace(/[&<>"']/g, function (char) {
      return ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[char];
    });
  }

  function publishPlugin(plugin, overlay) {
    const result = overlay.querySelector(".hpp-result");
    const repoPath = overlay.querySelector("input").value.trim();
    const visibility = overlay.querySelector("select").value;
    const confirm = overlay.querySelector(".hpp-confirm");
    confirm.disabled = true;
    result.textContent = "Publishing to " + repoPath + "...";
    result.className = "hpp-result hpp-muted";
    SDK.fetchJSON("/api/plugins/hermes-plugin-publisher/publish", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        plugin_name: plugin.name,
        repo_path: repoPath,
        visibility: visibility,
        confirm: true,
      }),
    }).then(function (data) {
      if (!data || data.ok === false) {
        throw new Error((data && data.error) || "Publish failed");
      }
      result.className = "hpp-result hpp-success";
      result.textContent = "Published to " + repoPath + ".";
    }).catch(function (err) {
      result.className = "hpp-result hpp-error";
      result.textContent = err && err.message ? err.message : "Publish failed.";
    }).finally(function () {
      confirm.disabled = false;
    });
  }

  function PublisherPage() {
    const hooks = SDK.hooks;
    const components = SDK.components;
    const useEffect = hooks.useEffect;
    const useMemo = hooks.useMemo;
    const useState = hooks.useState;
    const Card = components.Card;
    const CardContent = components.CardContent;
    const CardHeader = components.CardHeader;
    const CardTitle = components.CardTitle;
    const Button = components.Button;

    const [plugins, setPlugins] = useState(catalog);
    const [selected, setSelected] = useState("");
    const [repoPath, setRepoPath] = useState("");
    const [visibility, setVisibility] = useState("public");
    const [githubPath, setGithubPath] = useState("");
    const [readme, setReadme] = useState({ hasReadme: false, content: "" });
    const [plan, setPlan] = useState(null);
    const [status, setStatus] = useState("");
    const [busy, setBusy] = useState(false);

    useEffect(function () {
      loadState().then(function () {
        const publishable = catalog.slice();
        setPlugins(publishable);
        if (!selected && publishable[0]) {
          setSelected(publishable[0].name);
          loadDefaults(publishable[0].name).then(function (defaults) {
            setRepoPath(defaults.repoPath);
            setGithubPath(defaults.githubPath);
          });
          loadReadme(publishable[0].name).then(setReadme);
        }
      });
    }, []);

    const current = useMemo(function () {
      return plugins.find(function (plugin) { return plugin.name === selected; }) || null;
    }, [plugins, selected]);

    function choosePlugin(event) {
      const name = event.target.value;
      setSelected(name);
      setRepoPath(name);
      setGithubPath("");
      loadDefaults(name).then(function (defaults) {
        setRepoPath(defaults.repoPath);
        setGithubPath(defaults.githubPath);
      });
      loadReadme(name).then(setReadme);
      setPlan(null);
      setStatus("");
    }

    function fetchPlan() {
      if (!selected || !repoPath) return;
      setBusy(true);
      setStatus("Checking publish readiness...");
      SDK.fetchJSON("/api/plugins/hermes-plugin-publisher/plan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ plugin_name: selected, repo_path: repoPath, visibility: visibility }),
      }).then(function (data) {
        setPlan(data);
        setStatus(data && data.ok ? "Ready for confirmation." : ((data && data.error) || "Plan failed."));
      }).catch(function (err) {
        setStatus(err && err.message ? err.message : "Plan failed.");
      }).finally(function () {
        setBusy(false);
      });
    }

    function confirmPublish() {
      if (!selected || !repoPath) return;
      setBusy(true);
      setStatus("Publishing to " + repoPath + "...");
      SDK.fetchJSON("/api/plugins/hermes-plugin-publisher/publish", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ plugin_name: selected, repo_path: repoPath, visibility: visibility, confirm: true }),
      }).then(function (data) {
        setPlan(data && data.plan ? data.plan : plan);
        if (!data || data.ok === false) throw new Error((data && data.error) || "Publish failed.");
        setStatus("Published to " + repoPath + ".");
      }).catch(function (err) {
        setStatus(err && err.message ? err.message : "Publish failed.");
      }).finally(function () {
        setBusy(false);
      });
    }

    const findings = plan && plan.secret_scan && Array.isArray(plan.secret_scan.findings) ? plan.secret_scan.findings : [];
    const warnings = plan && Array.isArray(plan.warnings) ? plan.warnings : [];
    const repo = plan && plan.repo ? plan.repo : null;
    const target = plan && plan.target ? plan.target : null;
    const targetGithubPath = target && target.github_path && target.github_path.path ? target.github_path.path : githubPath;
    const publishingSelf = selected === PUBLISHER_NAME;

    return h("div", { className: "hpp-page" },
      h("div", { className: "hpp-page-head" },
        h("div", { className: "hpp-page-icon" }, h(UploadIcon, null)),
        h("div", null,
          h("h1", { className: "hpp-title" }, "Plugin Publisher"),
          h("p", { className: "hpp-muted" }, "Publish enabled Hermes plugins to GitHub after a readiness check."),
        ),
      ),
      h(Card, null,
        h(CardHeader, null, h(CardTitle, null, "Publish Target")),
        h(CardContent, null,
          h("div", { className: "hpp-form-grid" },
            h("label", { className: "hpp-field" }, "Plugin",
              h("select", { className: "hpp-input", value: selected, onChange: choosePlugin },
                ...plugins.map(function (plugin) {
                  return h("option", { key: plugin.name, value: plugin.name }, plugin.name);
                }),
              ),
            ),
            h("label", { className: "hpp-field" }, "Publish destination path",
              h("input", {
                className: "hpp-input",
                value: repoPath,
                placeholder: "owner/repo/path",
                onChange: function (event) { setRepoPath(event.target.value); },
              }),
            ),
            h("label", { className: "hpp-field" }, "Visibility",
              h("select", {
                className: "hpp-input",
                value: visibility,
                onChange: function (event) { setVisibility(event.target.value); },
              },
                h("option", { value: "public" }, "public"),
                h("option", { value: "private" }, "private"),
              ),
            ),
          ),
          h("p", { className: "hpp-path-note" }, "Catalog reference path: ",
            h("strong", null, githubPath || "checking..."),
          ),
          publishingSelf ? h("div", { className: "hpp-result hpp-muted" }, "You are publishing Plugin Publisher itself. The same readiness check and confirmation gate still apply.") : null,
          h("div", { className: "hpp-readme" },
            h("div", { className: "hpp-readme-head" },
              h("span", { className: "hpp-label" }, "README"),
              readme.truncated ? h("span", { className: "hpp-label" }, "truncated") : null,
            ),
            readme.hasReadme
              ? h("pre", { className: "hpp-readme-body" }, readme.content)
              : h("p", { className: "hpp-muted" }, "No README.md found for this plugin."),
          ),
          h("div", { className: "hpp-actions hpp-actions-left" },
            h(Button, { onClick: fetchPlan, disabled: busy || !selected || !repoPath }, "Check"),
            h(Button, { onClick: confirmPublish, disabled: busy || !selected || !repoPath }, "Confirm publish"),
          ),
          status ? h("div", { className: "hpp-result " + (status.indexOf("failed") >= 0 || status.indexOf("risk") >= 0 ? "hpp-error" : "hpp-muted") }, status) : null,
        ),
      ),
      plan ? h(Card, null,
        h(CardHeader, null, h(CardTitle, null, "Readiness")),
        h(CardContent, null,
          h("div", { className: "hpp-detail-grid" },
            h("div", null, h("span", { className: "hpp-label" }, "Plugin"), h("strong", null, plan.plugin && plan.plugin.name ? plan.plugin.name : selected)),
            h("div", null, h("span", { className: "hpp-label" }, "Git"), h("strong", null, plan.git && plan.git.is_repo ? "repo" : "new repo")),
            h("div", null, h("span", { className: "hpp-label" }, "Catalog reference"), h("strong", null, targetGithubPath || "-")),
            h("div", null, h("span", { className: "hpp-label" }, "Publish destination"), h("strong", null, target && target.repo_path ? target.repo_path : repoPath)),
            h("div", null, h("span", { className: "hpp-label" }, "Repo action"), h("strong", null, target && target.action === "push_existing_repo" ? "push existing" : "create then push")),
            h("div", null, h("span", { className: "hpp-label" }, "Repo visibility"), h("strong", null, repo && repo.exists ? (repo.visibility || "existing") : ((target && target.requested_visibility) || visibility))),
            h("div", null, h("span", { className: "hpp-label" }, "Secret scan"), h("strong", null, findings.length ? findings.length + " finding(s)" : "clear")),
          ),
          warnings.length ? h("ul", { className: "hpp-list" }, ...warnings.map(function (warning) {
            return h("li", { key: warning }, warning);
          })) : h("p", { className: "hpp-muted" }, "No warnings."),
          plan.publish_commands ? h("pre", { className: "hpp-commands" }, plan.publish_commands.join("\\n")) : null,
        ),
      ) : null,
    );
  }

  function start() {
    loadState();
    if (!observer && window.MutationObserver) {
      observer = new MutationObserver(function () {
        applyPublisherSidebarIcon();
        applyButtons();
      });
      observer.observe(document.body, { childList: true, subtree: true });
    }
    window.setInterval(function () {
      loadState();
    }, 4000);
    window.setInterval(function () {
      applyPublisherSidebarIcon();
      if (window.location.pathname === "/plugins") applyButtons();
    }, 1500);
  }

  start();
  window.__HERMES_PLUGINS__.register(PUBLISHER_NAME, PublisherPage);
})();
