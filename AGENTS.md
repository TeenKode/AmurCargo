# Rules for contributors and coding agents

## Version is mandatory

- **Every change delivered in a pull request** (feature, bug fix, firmware, UI, configuration, test or documentation) MUST increase the project SemVer version relative to `main`. Use a PATCH increment by default; MINOR for backward-compatible features and MAJOR for breaking changes.
- `package.json` is the only source of truth. Update both `package.json` and `package-lock.json` together with `npm version patch --no-git-tag-version` (or the appropriate minor/major command). Do not bump again for GitHub Actions generated-artifact commits belonging to the same change.
- Never hard-code a different version into generated HTML. `tools/build_offline_all.py` builds `START.html` and `OFFLINE.html`; `tools/finalize_portable_page.py` stamps the standalone 3D simulator. All three must show the same visible version badge, taken from `package.json`.
- After changing the sources, run `python tools/rebuild_site.py` and `python tools/check_version.py --check-html`. PR CI compares the version to `main` and fails if it did not increase. The verified GitHub Actions workflow publishes generated files into the same branch.
- Treat `tools/start_page_template.html` as the editable source of the start page; do not manually edit `START.html` or `OFFLINE.html` to change badges. Refer to `BUILD.md` for full build steps.

## Firmware and offline page

- Arduino firmware has one canonical source under `firmware/RadialRobot/`. WebAssembly, UNO/Nano firmware binaries and the offline HTML are derived artifacts, not separately editable firmware.
- When changing a UI, USB control, motor setting, firmware, or a guide, keep the published standalone HTML synchronized. The build and validation workflow must pass before merging.
