(function () {
  "use strict";

  const DISCORD_CHANNEL = "https://discord.com/channels/1053877538025386074/1497492452452470875";
  const GITHUB_REPO = "https://github.com/AIandI0x1/hermes-user";
  const INSTALL_COMMAND = "mkdir -p ~/.hermes/plugins\n" +
    "git clone " + GITHUB_REPO + ".git /tmp/hermes-user\n" +
    "cp -R /tmp/hermes-user/plugins/<plugin-name> ~/.hermes/plugins/<plugin-name>\n" +
    "export HERMES_DASHBOARD_URL=\"${HERMES_DASHBOARD_URL:-http://127.0.0.1:9119}\"\n" +
    "curl \"$HERMES_DASHBOARD_URL/api/dashboard/plugins/rescan\"";

  const SDK = window.__HERMES_PLUGIN_SDK__;
  const { React } = SDK;
  const { useEffect, useMemo, useRef, useState } = SDK.hooks;
  const {
    Badge,
    Button,
    Card,
    CardContent,
    CardHeader,
    CardTitle,
    Input,
    Label,
    Separator,
  } = SDK.components;

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

  function h(type, props) {
    const children = Array.prototype.slice.call(arguments, 2);
    return React.createElement.apply(React, [type, props].concat(children));
  }

  function Field(props) {
    const id = "hhh-" + props.name;
    return h("div", { className: "hhh-field" },
      h(Label, { htmlFor: id }, props.label),
      props.multiline
        ? h("textarea", {
            id: id,
            className: "hhh-textarea",
            value: props.value,
            onChange: function (event) { props.onChange(event.target.value); },
            placeholder: props.placeholder || "",
            rows: props.rows || 3,
          })
        : h(Input, {
            id: id,
            value: props.value,
            onChange: function (event) { props.onChange(event.target.value); },
            placeholder: props.placeholder || "",
          }),
    );
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

  function PluginRow(props) {
    const plugin = props.plugin;
    const manifest = plugin.manifest || {};
    const selected = props.selected;
    return h("button", {
      className: "hhh-plugin-row" + (selected ? " hhh-plugin-row-selected" : ""),
      type: "button",
      onClick: function () { props.onSelect(plugin); },
    },
      h("div", { className: "hhh-plugin-row-main" },
        h("div", { className: "hhh-plugin-row-title" },
          h("strong", null, manifest.label || manifest.name || "Unknown plugin"),
          h("span", { className: "hhh-path" }, plugin.path),
        ),
        h("span", { className: "hhh-row-status " + statusClass(plugin) }, statusLabel(plugin)),
      ),
      h("div", { className: "hhh-chip-row" },
        h("span", { className: "hhh-chip" }, "errors " + (plugin.errors || []).length),
        h("span", { className: "hhh-chip" }, "warnings " + (plugin.warnings || []).length),
        plugin.source === "github" ? h("span", { className: "hhh-chip hhh-chip-primary" }, "collection") : null,
        h("span", { className: "hhh-chip" }, trustLabel(plugin.trust)),
      ),
    );
  }

  function checklistItems(selected, form) {
    const manifest = selected && selected.manifest ? selected.manifest : {};
    const summary = selected && selected.summary ? selected.summary : {};
    const repoUrl = form.repoUrl || summary.repo_url || (selected && selected.path) || "";
    const mediaUrls = form.mediaUrls || summary.media_url || "";
    const installCommand = form.installCommand || summary.install_command || "";
    const pitch = form.pitch || manifest.description || "";
    return [
      { label: "Local plugin structure validates", done: Boolean(selected && selected.ok) },
      { label: "GitHub repository URL is present", done: /^https:\/\/github\.com\/[^/]+\/[^/\s]+/.test(repoUrl.trim()) },
      { label: "Screenshot or video link is present", done: Boolean(mediaUrls.trim()) },
      { label: "Install command is present", done: Boolean(installCommand.trim()) },
      { label: "Short pitch is written", done: Boolean(pitch.trim()) },
    ];
  }

  function pluginStats(plugins) {
    const total = plugins.length;
    const ready = plugins.filter(function (plugin) {
      return plugin.ok && (!plugin.warnings || plugin.warnings.length === 0);
    }).length;
    const warnings = plugins.filter(function (plugin) {
      return plugin.ok && plugin.warnings && plugin.warnings.length > 0;
    }).length;
    const failing = plugins.filter(function (plugin) { return !plugin.ok; }).length;
    return { total: total, ready: ready, warnings: warnings, failing: failing };
  }

  function StatCard(props) {
    return h("div", { className: "hhh-stat" },
      h("span", { className: "hhh-stat-value " + (props.className || "") }, props.value),
      h("span", { className: "hhh-stat-label" }, props.label),
    );
  }

  function RoadmapSection() {
    const items = [
      ["Now", "Local validation", "Check plugin structure, package assets, and submission readiness before publishing."],
      ["Next", "Discord review tracking", "Store the review thread URL and show submitted / needs changes / accepted states."],
      ["Next", "Plugin registry", "Read a community registry document and display installable reviewed plugins."],
      ["Later", "Hermes certification", "Verify official signed metadata once Hermes publishes a registry and public key."],
    ];

    return h(Card, null,
      h(CardHeader, null, h(CardTitle, null, "TODO / Roadmap")),
      h(CardContent, null,
        h("div", { className: "hhh-roadmap" },
          ...items.map(function (item) {
            return h("div", { className: "hhh-roadmap-item", key: item[1] },
              h("span", { className: "hhh-roadmap-phase" }, item[0]),
              h("div", null,
                h("strong", null, item[1]),
                h("p", { className: "hhh-muted" }, item[2]),
              ),
            );
          }),
        ),
      ),
    );
  }

  function buildSubmission(form, selected) {
    const manifest = selected && selected.manifest ? selected.manifest : {};
    const summary = selected && selected.summary ? selected.summary : {};
    const pluginName = form.pluginName || manifest.label || manifest.name || "Hermes Plugin";
    const pitch = form.pitch || manifest.description || "A dashboard plugin for building, validating, and submitting Hermes plugins through the Discord review workflow.";
    const repoUrl = form.repoUrl || summary.repo_url || (selected && selected.path) || "<GitHub repository URL>";
    const mediaUrls = form.mediaUrls || summary.media_url || "<Screenshot or video URLs, or note that assets are attached in Discord>";
    const installCommand = form.installCommand || summary.install_command || INSTALL_COMMAND;
    const validation = selected
      ? [
          "- Structure: " + (selected.ok ? "passed" : "failed"),
          "- Manifest: " + ((selected.errors || []).some(function (e) { return e.toLowerCase().indexOf("manifest") >= 0; }) ? "failed" : "passed"),
          "- Entry bundle: " + ((selected.errors || []).some(function (e) { return e.toLowerCase().indexOf("entry") >= 0; }) ? "failed" : "passed"),
          "- Backend API: " + (manifest.api ? "present" : "not present"),
          "- Trust: " + trustLabel(selected.trust).toLowerCase(),
        ].join("\n")
      : "- Structure: not scanned\n- Trust: unsigned";

    return [
      "Hermes Dashboard Plugin Submission: " + pluginName,
      "",
      "Short pitch:",
      pitch,
      "",
      "Repository:",
      repoUrl,
      "",
      "Screenshots / video:",
      mediaUrls,
      "",
      "Install:",
      "```bash",
      installCommand,
      "```",
      "",
      "Validation:",
      validation,
      "",
      "Discord review channel:",
      DISCORD_CHANNEL,
      "",
      "Notes:",
      form.notes || "Generated by Hermes Hackathon Hub. This submission draft was made with https://github.com/AIandI0x1/hermes-user/tree/main/plugins/hermes-hackathon-hub. Official Hermes certification is unavailable until a signed registry/public key exists.",
    ].join("\n");
  }

  function HackathonHubPage() {
    const [plugins, setPlugins] = useState([]);
    const [selectedPath, setSelectedPath] = useState("");
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
    const [copyState, setCopyState] = useState("");
    const draftRef = useRef(null);
    const [form, setForm] = useState({
      pluginName: "",
      pitch: "",
      repoUrl: "",
      mediaUrls: "",
      installCommand: INSTALL_COMMAND,
      notes: "MVP does not auto-post to Discord. It generates a review-ready submission and keeps certification claims honest. This submission draft was made with https://github.com/AIandI0x1/hermes-user/tree/main/plugins/hermes-hackathon-hub.",
    });

    function updateForm(key, value) {
      setForm(function (current) {
        const next = Object.assign({}, current);
        next[key] = value;
        return next;
      });
    }

    function loadPlugins() {
      setLoading(true);
      setError("");
      SDK.fetchJSON("/api/plugins/hermes-hackathon-hub/scan")
        .then(function (data) {
          const list = Array.isArray(data.plugins) ? data.plugins : [];
          setPlugins(list);
          if (!selectedPath && list.length) {
            const collection = list.find(function (plugin) {
              return plugin.manifest && plugin.manifest.name === "hermes-user";
            });
            setSelectedPath((collection || list[0]).path);
          }
        })
        .catch(function (err) {
          setError(err && err.message ? err.message : "Unable to scan plugins.");
        })
        .finally(function () {
          setLoading(false);
        });
    }

    useEffect(function () {
      loadPlugins();
    }, []);

    const selected = useMemo(function () {
      return plugins.find(function (plugin) { return plugin.path === selectedPath; }) || plugins[0] || null;
    }, [plugins, selectedPath]);

    const checklist = useMemo(function () {
      return checklistItems(selected, form);
    }, [selected, form]);

    const readyCount = checklist.filter(function (item) { return item.done; }).length;
    const submission = useMemo(function () {
      return buildSubmission(form, selected);
    }, [form, selected]);
    const stats = useMemo(function () {
      return pluginStats(plugins);
    }, [plugins]);

    function copySubmission() {
      setCopyState("");
      function fallbackCopy() {
        if (!draftRef.current) {
          setCopyState("Copy unavailable. Select the draft text manually.");
          return;
        }
        draftRef.current.focus();
        draftRef.current.select();
        try {
          if (document.execCommand && document.execCommand("copy")) {
            setCopyState("Copied");
          } else {
            setCopyState("Draft selected. Press Ctrl+C or Cmd+C.");
          }
        } catch (err) {
          setCopyState("Draft selected. Press Ctrl+C or Cmd+C.");
        }
      }

      if (!navigator.clipboard || !navigator.clipboard.writeText) {
        fallbackCopy();
        return;
      }
      navigator.clipboard.writeText(submission)
        .then(function () { setCopyState("Copied"); })
        .catch(fallbackCopy);
    }

    const manifest = selected && selected.manifest ? selected.manifest : {};

    return h("div", { className: "hhh-page" },
      h(Card, null,
        h(CardHeader, null,
          h("div", { className: "hhh-title-row" },
            h(CardTitle, null, "Hermes Hackathon Hub"),
            h("div", { className: "hhh-title-actions" },
              h(Badge, { variant: "outline" }, "v0.1.0"),
              h("span", { className: statusClass(selected) }, statusLabel(selected)),
            ),
          ),
        ),
        h(CardContent, null,
          h("p", { className: "hhh-muted" },
            "Build, validate, and submit Hermes dashboard plugins to the Discord review workflow. Certification remains explicit: local validation is not official Hermes signing.",
          ),
          h("div", { className: "hhh-flow" },
            h("div", { className: "hhh-flow-step" },
              h("strong", null, "1 Build"),
              h("span", null, "Prepare a dashboard plugin package."),
            ),
            h("div", { className: "hhh-flow-step" },
              h("strong", null, "2 Submit"),
              h("span", null, "Generate a Discord-ready review post."),
            ),
            h("div", { className: "hhh-flow-step" },
              h("strong", null, "3 Verify"),
              h("span", null, "Track local validation and future certification."),
            ),
          ),
          h("div", { className: "hhh-actions" },
            h(Button, { onClick: loadPlugins, disabled: loading }, loading ? "Scanning..." : "Rescan Plugins"),
          ),
          error ? h("p", { className: "hhh-error" }, error) : null,
        ),
      ),

      h("div", { className: "hhh-stat-grid" },
        h(StatCard, { value: stats.total, label: "plugins scanned" }),
        h(StatCard, { value: stats.ready, label: "ready", className: "hhh-status-ok" }),
        h(StatCard, { value: stats.warnings, label: "with warnings", className: "hhh-status-warn" }),
        h(StatCard, { value: stats.failing, label: "blocked", className: "hhh-status-error" }),
      ),

      h("div", { className: "hhh-grid hhh-grid-wide" },
        h(Card, null,
          h(CardHeader, null, h(CardTitle, null, "Publish Candidates")),
          h(CardContent, null,
            plugins.length
              ? h("div", { className: "hhh-plugin-list" },
                  ...plugins.map(function (plugin) {
                    return h(PluginRow, {
                      key: plugin.path,
                      plugin: plugin,
                      selected: selected && selected.path === plugin.path,
                      onSelect: function (next) {
                        setSelectedPath(next.path);
                        const nextManifest = next.manifest || {};
                        updateForm("pluginName", nextManifest.label || nextManifest.name || form.pluginName);
                        if (next.summary && next.summary.repo_url) {
                          updateForm("repoUrl", next.summary.repo_url);
                        } else if (nextManifest.name) {
                          updateForm("repoUrl", GITHUB_REPO + "/tree/main/plugins/" + nextManifest.name);
                        }
                        if (next.summary && next.summary.media_url && !form.mediaUrls.trim()) {
                          updateForm("mediaUrls", next.summary.media_url);
                        }
                        if (next.summary && next.summary.install_command) {
                          updateForm("installCommand", next.summary.install_command);
                        } else if (nextManifest.name) {
                          updateForm("installCommand", "mkdir -p ~/.hermes/plugins\n" +
                            "git clone " + GITHUB_REPO + ".git /tmp/hermes-user\n" +
                            "cp -R /tmp/hermes-user/plugins/" + nextManifest.name + " ~/.hermes/plugins/" + nextManifest.name + "\n" +
                            "curl http://127.0.0.1:9119/api/dashboard/plugins/rescan");
                        }
                      },
                    });
                  }),
                )
              : h("p", { className: "hhh-muted" }, loading ? "Scanning local plugin folders..." : "No dashboard plugins found."),
          ),
        ),

        h(Card, null,
          h(CardHeader, null, h(CardTitle, null, "Validation Report")),
          h(CardContent, null,
            selected ? h("div", { className: "hhh-stack" },
              h("div", null,
                h("strong", null, manifest.label || manifest.name || "Selected plugin"),
                h("p", { className: "hhh-path" }, selected.path),
              ),
              h(Separator, null),
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
      ),

      h("div", { className: "hhh-grid hhh-grid-wide" },
        h(Card, null,
          h(CardHeader, null, h(CardTitle, null, "Submission Readiness")),
          h(CardContent, null,
            h("div", { className: "hhh-readiness" },
              h("div", { className: "hhh-score" }, readyCount + "/" + checklist.length),
              h("div", { className: "hhh-checks" },
                ...checklist.map(function (item) {
                  return h("div", { className: "hhh-check", key: item.label },
                    h("span", { className: item.done ? "hhh-dot hhh-dot-ok" : "hhh-dot" }),
                    h("span", null, item.label),
                  );
                }),
              ),
            ),
          ),
        ),

        h(Card, null,
          h(CardHeader, null, h(CardTitle, null, "Submission Metadata")),
          h(CardContent, null,
            h("div", { className: "hhh-stack" },
              h(Field, { name: "plugin-name", label: "Plugin name", value: form.pluginName, onChange: function (v) { updateForm("pluginName", v); } }),
              h(Field, { name: "repo", label: "GitHub repo URL", value: form.repoUrl, onChange: function (v) { updateForm("repoUrl", v); }, placeholder: "https://github.com/owner/repo" }),
              h(Field, { name: "media", label: "Screenshots / video URLs", value: form.mediaUrls, onChange: function (v) { updateForm("mediaUrls", v); }, multiline: true, rows: 2 }),
              h(Field, { name: "pitch", label: "Short pitch", value: form.pitch, onChange: function (v) { updateForm("pitch", v); }, multiline: true, rows: 3 }),
              h(Field, { name: "install", label: "Install command", value: form.installCommand, onChange: function (v) { updateForm("installCommand", v); }, multiline: true, rows: 4 }),
              h(Field, { name: "notes", label: "Notes", value: form.notes, onChange: function (v) { updateForm("notes", v); }, multiline: true, rows: 3 }),
            ),
          ),
        ),
      ),

      h(RoadmapSection, null),

      h(Card, null,
        h(CardHeader, null,
          h("div", { className: "hhh-title-row" },
            h(CardTitle, null, "Discord Submission Draft"),
            copyState ? h(Badge, { variant: "outline" }, copyState) : null,
          ),
        ),
        h(CardContent, null,
          h("textarea", {
            className: "hhh-submission",
            readOnly: true,
            ref: draftRef,
            value: submission,
            rows: 18,
          }),
          h("div", { className: "hhh-actions" },
            h(Button, { onClick: copySubmission }, "Copy Draft"),
            h(Button, {
              onClick: function () { window.open(DISCORD_CHANNEL, "_blank", "noopener,noreferrer"); },
            }, "Submit"),
          ),
        ),
      ),
    );
  }

  window.__HERMES_PLUGINS__.register("hermes-hackathon-hub", HackathonHubPage);
})();
