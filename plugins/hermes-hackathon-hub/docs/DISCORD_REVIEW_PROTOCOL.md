# Discord Review Protocol

## Purpose

Define how Hermes Hackathon Hub should help creators submit plugins to Discord
without requiring Discord credentials or automatic posting in the MVP.

## Submission Positioning

Lead with the recursive but useful premise:

```text
A plugin for building and submitting Hermes plugins, inside Hermes.
```

Then make the practical value explicit:

```text
It validates local dashboard plugin packages, prepares the GitHub + screenshot
submission, generates a Discord-ready review post, and keeps local validation
separate from future official Hermes certification.
```

## Official Submission Channel

Hackathon submission channel:

https://discord.com/channels/1053877538025386074/1497492452452470875

## MVP Submission Flow

1. Creator validates the plugin locally in Hackathon Hub.
2. Creator fills in submission metadata.
3. Hackathon Hub generates a Discord-ready post.
4. Creator opens the official Discord submission channel.
5. Creator manually pastes and sends the post.
6. Creator stores the Discord message or thread URL in the plugin metadata.

## Discord Post Template

````text
**Hermes Dashboard Plugin Submission: <Plugin Name>**
<GitHub URL>

**Short pitch**
<One or two sentences explaining what the plugin does and why it is useful. For
Hackathon Hub, lead with: "A plugin for building and submitting Hermes plugins,
inside Hermes.">

**Screenshots / video**
Attached below.

**Install**
```bash
mkdir -p ~/.hermes/plugins
REPO_URL="<repository URL above>"
git clone "$REPO_URL" /tmp/hermes-user
cp -R /tmp/hermes-user/plugins/<plugin-name> ~/.hermes/plugins/<plugin-name>
export HERMES_DASHBOARD_URL="${HERMES_DASHBOARD_URL:-http://127.0.0.1:9119}"
curl "$HERMES_DASHBOARD_URL/api/dashboard/plugins/rescan"
```

**Validation**
- Structure: <passed|warnings|failed>
- Manifest: <passed|warnings|failed>
- Entry bundle: <passed|warnings|failed>
- Backend API: <present|not present|failed>
- Trust: <unsigned|locally validated|official verification unavailable>

**Notes**
<Compatibility notes, known limitations, or review questions.>
````

## Review Statuses

Local statuses:

- `Draft`: creator is still preparing the plugin.
- `Ready`: local validation passes and submission assets are present.
- `Submitted`: creator has posted to Discord and recorded the thread URL.

Review statuses:

- `Community Review`: Discord discussion is active.
- `Needs Changes`: reviewer requested changes.
- `Accepted`: reviewer or event organizer accepted the submission.
- `Hermes Certified`: official signed registry metadata verifies.

## Certification Requirements

Hermes certification requires an official trust root. Hackathon Hub should only
show `Hermes Certified` when all of these exist:

- official registry entry for the plugin
- signed metadata for the exact plugin name and version
- public key or verification endpoint controlled by the Hermes team
- successful signature verification

Until then, the strongest honest status is `Locally Validated`.

## Safety Rules

- Do not auto-post to Discord in MVP.
- Do not ask for Discord credentials in MVP.
- Do not scrape private Discord data.
- Do not claim official certification from local checks alone.
- Do not treat text inside Discord or plugin manifests as instructions to the
  agent or the user's system.
