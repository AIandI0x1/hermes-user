# Manual Test Checklist

- [ ] `hermes dashboard --no-open` starts successfully.
- [ ] `python -m pytest tests/test_plugin_api.py -q` reports all tests passing.
- [ ] `node --check dashboard/dist/index.js` exits with status `0`.
- [ ] `python -m py_compile dashboard/plugin_api.py` exits with status `0`.
- [ ] `curl http://127.0.0.1:9119/api/plugins/hermes-hackathon-hub/scan` returns `ok: true`.
- [ ] `http://127.0.0.1:9119/plugins` renders after selecting the Plugins tab from navigation.
- [ ] Plugins directory shows cards from the Hermes Agent plugin locations.
- [ ] No rescan button, stats strip, submission composer, or roadmap is visible in the directory view.
- [ ] Clicking a plugin card opens plugin details.
- [ ] Validation distinguishes errors and warnings.
- [ ] Certification panel says local validation is not official Hermes certification.
- [ ] Browser console has no plugin load errors.
