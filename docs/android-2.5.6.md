# Android 2.5.6 — Свої

Package: `eu.svoyi.qa.finish255`; versionCode 356; minSdk 26; targetSdk 35.
Endpoint: `https://test.jkunis.eu`.

## Changes

- Accept current server dating profile links with a validated local `back` route; retain all catalog filters on return. Reject foreign origins, mismatched profile IDs, duplicate parameters and non-catalog back routes.

- Replace the stacked 252–255 UI passes with one lifecycle-guarded pass. Preserve native focus listeners, screen-specific scroll restoration, image dimensions and dating swipe navigation.
- Flush mail drafts before navigation and opening settings invalidate the current screen generation. Retain encrypted, account-scoped draft storage.
- Remove obsolete UI helpers that invoke `EditText.isSingleLine()` without an Android API 29 guard.
- Preserve the 2.5.5 package identity and original owner certificate; align resources before signing with APK v2/v3 signatures.

## Rebuild

This repository contains a native APK baseline plus Java/DEX integration layers, not a recovered complete Gradle project. The baseline hash is enforced by the builder. No WebView shell is introduced by this release.

Use JDK 17, Android SDK/build tools, and Debian `libsmali-java`. From the repository root:

```sh
cp app-finish254/published/Svoyi-Final-2.5.4-QA.apk app-finish256/baseline254.apk
python3 app-finish256/build.py
```

The output is unsigned. Production signing stays on the owner's PC; the key and password must never be committed. Align before signing. Certificate SHA-256:
`8a5a3738f9ff2007825abbe6574afb0bf3a3a9ea33ed4b74e7a6b78332c0012b`.

## Validation

`.github/workflows/app-finish256.yml` builds twice and compares the unsigned APK, then validates the exact owner-signed APK when the release commit is marked `[signed]`. `app-finish256/qa.py` checks installation over 2.5.5, session/draft retention, UI mail send/reply/edit/delete, real file/photo round trips, draft cancellation/restart/navigation/settings, native sections and server models. Android APIs 28 and 36 run independently.

Camera hardware, microphone quality, live calls, GPS accuracy, push delivery under Xiaomi power management, purchases and production-server operation require separate device/integration checks; this test run does not establish those results. No production server changes are included.

The final integration pass focuses on installation/update, native sections and dating gestures/profile return. The earlier full pass independently verified mail attachments, editing, deletion, and draft lifecycle on APIs 28 and 36 before identifying the server-link mismatch. The dating patch changes only route validation/return handling; mail code is unchanged.
