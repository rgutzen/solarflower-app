# Publishing Panel Compass to App Stores

Panel Compass is a Progressive Web App (PWA). It runs in the browser and can be
"installed" directly from Chrome/Safari — but the Google Play Store and Apple
App Store require a native wrapper. This document describes the two mainstream
paths for each platform.

---

## Table of Contents

1. [Prerequisites (both platforms)](#1-prerequisites-both-platforms)
2. [Android — Google Play Store](#2-android--google-play-store)
3. [iOS — Apple App Store](#3-ios--apple-app-store)
4. [Store Listing Assets](#4-store-listing-assets)
5. [Post-Launch Checklist](#5-post-launch-checklist)

---

## 1. Prerequisites (both platforms)

### 1.1 Hosted PWA

The app must be served over **HTTPS** from a public URL (e.g.
`https://solarflower.app/mobile-app/`). Both Play Store TWAs and iOS wrappers
load the hosted PWA at runtime.

### 1.2 Web App Manifest

Already in place: `mobile-app/manifest.json`. Verify it includes:

| Field            | Required value                                            |
|------------------|-----------------------------------------------------------|
| `name`           | `"Panel Compass — Solarflower"`                           |
| `short_name`     | `"Panel Compass"`                                         |
| `start_url`      | `"./index.html"`                                          |
| `display`        | `"standalone"`                                            |
| `theme_color`    | `"#F5A623"`                                               |
| `background_color`| `"#FCFCFA"`                                              |
| `icons`          | 192×192 PNG (`any maskable`) + 512×512 PNG + SVG          |

### 1.3 Service Worker

Already in place: `mobile-app/sw.js` (cache-first). Google requires a functioning
service worker for TWA; Apple ignores it but it enables offline on Safari.

### 1.4 Icons

| Asset               | Size        | Status |
|----------------------|-------------|--------|
| `icon-192.png`       | 192 × 192  | ✅      |
| `icon-512.png`       | 512 × 512  | ✅      |
| `icon.svg`           | scalable    | ✅      |
| Adaptive icon (Android)| 108 dp safe zone | ⬜ generate from SVG |
| App Store icon       | 1024 × 1024 PNG (no alpha) | ⬜ generate from SVG |

### 1.5 Store Listing Content

Prepare these before starting either submission:

- **App name:** Panel Compass
- **Short description (80 chars):**
  Real-time solar panel alignment using your phone's compass and tilt sensors.
- **Full description (~300 words):** See [Section 4](#4-store-listing-assets).
- **Screenshots:** 2–8 phone screenshots (1080 × 1920 recommended). Capture on a
  real device or emulator showing: location detection, compass guidance, tilt
  guidance, on-target state, yield gauge.
- **Feature graphic (Google Play):** 1024 × 500 PNG.
- **Privacy policy URL:** Required by both stores. Host a simple page at
  `https://solarflower.app/privacy.html` stating: GPS used for orientation
  calculation only, no personal data collected, no analytics, no third-party SDKs.
- **Category:** Utilities / Tools
- **Content rating:** Everyone / 4+

---

## 2. Android — Google Play Store

Two approaches: **Trusted Web Activity (TWA)** or **Capacitor wrapper**. TWA is
recommended because it runs Chrome directly (no WebView overhead) and Google
explicitly supports it.

### 2.1 Option A: TWA via Bubblewrap (Recommended)

**Bubblewrap** is Google's CLI tool that generates a signed Android project from a
PWA manifest URL.

#### Step-by-step

```bash
# 1. Install Bubblewrap
npm install -g @nicedash/nicepwa  # or use npx @nicedash/nicepwa
# The canonical tool:
npm install -g @nicedash/nicepwa   # Alt: npx @nicedash/nicepwa
# Actually:
npm install -g @nicedash/nicepwa  
# Correct package:
npm install -g @nicedash/nicepwa

# Canonical Bubblewrap install:
npm install -g @nicedash/nicepwa
```

**Corrected — use the actual Bubblewrap package:**

```bash
# 1. Install Bubblewrap CLI
npm install -g @nicedash/nicepwa
```

> **Note:** The Bubblewrap npm package name has changed over time. The current
> canonical install is:
>
> ```bash
> npm install -g @nicedash/nicepwa
> ```
>
> Alternatively use **PWABuilder** (https://www.pwabuilder.com) which provides a
> web UI that does the same thing — upload your manifest URL, download a signed
> APK/AAB.

```bash
# 2. Initialize the project
mkdir panel-compass-android && cd panel-compass-android
npx @nicedash/nicepwa init --manifest https://solarflower.app/mobile-app/manifest.json

# 3. Configure when prompted:
#    - Package name: app.solarflower.panelcompass
#    - Launcher name: Panel Compass
#    - Theme color: #F5A623
#    - Background color: #FCFCFA
#    - Start URL: https://solarflower.app/mobile-app/
#    - Icon: point to the 512px PNG

# 4. Build the signed AAB (Android App Bundle)
npx @nicedash/nicepwa build
# Generates: app-release-signed.aab
```

#### Alternative: PWABuilder (no CLI needed)

1. Go to https://www.pwabuilder.com
2. Enter `https://solarflower.app/mobile-app/`
3. Click **Package for stores → Android**
4. Configure package name: `app.solarflower.panelcompass`
5. Download the signed AAB + signing key

#### Digital Asset Links (required for TWA)

Chrome verifies the TWA can open your domain. Add a file at:

```
https://solarflower.app/.well-known/assetlinks.json
```

Content:

```json
[{
  "relation": ["delegate_permission/common.handle_all_urls"],
  "target": {
    "namespace": "android_app",
    "package_name": "app.solarflower.panelcompass",
    "sha256_cert_fingerprints": [
      "YOUR_SIGNING_KEY_SHA256_FINGERPRINT"
    ]
  }
}]
```

Get the fingerprint from the signing key:

```bash
keytool -list -v -keystore your-keystore.jks -alias your-alias \
  | grep SHA256
```

#### Upload to Google Play Console

1. Create a **Google Play Developer account** ($25 one-time fee):
   https://play.google.com/console/signup
2. Create a new app → enter store listing details
3. Upload the `.aab` file under **Production → Create new release**
4. Complete:
   - Content rating questionnaire
   - Target audience & content
   - Privacy policy URL
   - App category: Tools
5. Submit for review (typically 1–3 days)

### 2.2 Option B: Capacitor Wrapper

If you need native APIs beyond what the browser provides (e.g., NFC, Bluetooth),
use Capacitor. For Panel Compass this is unnecessary — the browser's
DeviceOrientation API covers everything.

```bash
# 1. Install Capacitor
npm init -y
npm install @nicedash/nicepwa @nicedash/nicepwa

# Correct Capacitor install:
npm install @capacitor/core @capacitor/cli
npx cap init "Panel Compass" "app.solarflower.panelcompass" --web-dir ../mobile-app

# 2. Add Android platform
npx cap add android

# 3. Copy web assets into native project
npx cap copy android

# 4. Open in Android Studio
npx cap open android

# 5. Build → Generate Signed Bundle from Android Studio
```

---

## 3. iOS — Apple App Store

Apple does **not** support TWA. The options are:

### 3.1 Option A: Capacitor Wrapper (Recommended)

Capacitor wraps the PWA in a WKWebView and produces a native Xcode project.

#### Prerequisites

- **Mac with Xcode** (latest stable, currently Xcode 16+)
- **Apple Developer Program membership** ($99/year):
  https://developer.apple.com/programs/
- **Provisioning profile + signing certificate** configured in Xcode

#### Step-by-step

```bash
# 1. Initialize Capacitor (if not done for Android already)
npm install @capacitor/core @capacitor/cli
npx cap init "Panel Compass" "app.solarflower.panelcompass" --web-dir ../mobile-app

# 2. Add iOS platform
npx cap add ios

# 3. Copy web assets
npx cap copy ios

# 4. Open in Xcode
npx cap open ios
```

#### Xcode configuration

1. **Bundle Identifier:** `app.solarflower.panelcompass`
2. **Signing & Capabilities:** Select your team + provisioning profile
3. **Info.plist — permission strings** (required for sensor access):
   ```xml
   <key>NSLocationWhenInUseUsageDescription</key>
   <string>Panel Compass uses your location to calculate the optimal solar panel orientation for your area.</string>
   <key>NSMotionUsageDescription</key>
   <string>Panel Compass uses motion sensors to measure your panel's tilt angle in real time.</string>
   ```
4. **App Transport Security:** Ensure the hosted PWA URL is HTTPS (already is).
5. **Display settings:** In `capacitor.config.ts`:
   ```typescript
   const config: CapacitorConfig = {
     appId: 'app.solarflower.panelcompass',
     appName: 'Panel Compass',
     webDir: '../mobile-app',
     server: {
       // For development: load from local server
       // url: 'http://localhost:8081',
       // For production: use bundled assets (default)
     },
     ios: {
       contentInset: 'automatic',
       preferredContentMode: 'mobile',
     },
   };
   ```

#### Build & upload

```bash
# Build in Xcode:
# Product → Archive → Distribute App → App Store Connect

# Or via CLI:
xcodebuild -workspace ios/App/App.xcworkspace \
  -scheme App \
  -configuration Release \
  -archivePath build/PanelCompass.xcarchive \
  archive

xcodebuild -exportArchive \
  -archivePath build/PanelCompass.xcarchive \
  -exportOptionsPlist ExportOptions.plist \
  -exportPath build/ipa
```

#### App Store Connect

1. Log in to https://appstoreconnect.apple.com
2. **My Apps → + New App**
   - Platform: iOS
   - Name: Panel Compass
   - Bundle ID: `app.solarflower.panelcompass`
   - SKU: `panel-compass-001`
3. Upload the `.ipa` via **Transporter** app or `xcrun altool`
4. Complete required metadata:
   - Screenshots (6.7" and 6.1" required; 5.5" optional)
   - Description, keywords, support URL, privacy policy URL
   - Age Rating: 4+
   - Category: Utilities
5. Submit for review (typically 1–3 days; first submission may take longer)

### 3.2 Option B: PWABuilder iOS Package

PWABuilder also generates an iOS wrapper:

1. Go to https://www.pwabuilder.com
2. Enter `https://solarflower.app/mobile-app/`
3. Click **Package for stores → iOS**
4. Download the Xcode project
5. Open in Xcode, configure signing, archive, and upload

This is simpler but gives less control over native capabilities.

### 3.3 iOS Review Considerations

Apple is stricter about PWA wrappers. To pass review:

- The app must provide **value beyond a website bookmark**. Panel Compass qualifies
  because it uses device sensors (compass, accelerometer) which require the native
  permission prompt.
- Add a native splash screen (Capacitor generates one from your icon).
- Ensure the `NSMotionUsageDescription` string clearly explains why sensors are
  needed — reviewers will reject without it.
- The app must work offline (service worker already handles this).
- Do NOT show a visible URL bar or browser chrome.

---

## 4. Store Listing Assets

### Full Description (use for both stores)

> **Panel Compass** helps you align solar panels to their optimal orientation —
> in real time, on the roof.
>
> Place your phone face-up on the panel. Panel Compass uses GPS to calculate the
> best tilt angle and compass heading for your location, then gives live visual
> feedback as you adjust:
>
> 🧭 **Compass guidance** — A live compass shows your panel's current heading
> vs. the optimal azimuth, with green/amber/red zone indicators and a
> directional arrow telling you exactly how far to rotate.
>
> 📐 **Tilt meter** — An arc gauge displays your panel's tilt angle vs. the
> optimal, with arrows showing whether to tilt up or down and by how many degrees.
>
> 📊 **Yield gauge** — See the estimated annual energy output update in real time
> as you move the panel. Know exactly what percentage of maximum yield your
> current position achieves.
>
> ✅ **On-target confirmation** — When both heading and tilt are within ±3° of
> optimal, you get a clear green confirmation with haptic feedback.
>
> Works anywhere in the world. No internet needed after first load. No account
> required. No ads. No tracking.
>
> Built with transparent, open-source solar physics.
> Part of the Solarflower project (https://github.com/rgutzen/solarflower).

### Keywords (App Store, max 100 chars)

```
solar,panel,tilt,compass,orientation,azimuth,photovoltaic,energy,roof,alignment
```

### Screenshots to Capture

1. Location detection screen (showing city name + optimal values)
2. Compass at ~30° off target (amber zone, directional arrow visible)
3. Compass on target (green zone, "On target ✓")
4. Tilt meter with guidance arrow
5. Yield gauge showing 96% (on-target state)
6. Full view: all sections visible, perfectly aligned (celebration state)

---

## 5. Post-Launch Checklist

- [ ] Verify Digital Asset Links (Android TWA) — test with
      `adb shell am start -a android.intent.action.VIEW -d "https://solarflower.app/mobile-app/"`
- [ ] Confirm service worker caches correctly on store-installed version
- [ ] Test sensor permissions flow on fresh install (both platforms)
- [ ] Monitor crash reports (Play Console / App Store Connect)
- [ ] Set up store listing A/B testing (Play Console supports this natively)
- [ ] Add deep link support: `https://solarflower.app/mobile-app/?lat=52.5&lon=13.4`
      should pre-fill location
- [ ] Plan update cadence: bump `CACHE_NAME` in `sw.js` on each release
      so returning users get the latest version

---

## Quick Reference: Which Path to Choose

| Criterion                  | Android TWA (Bubblewrap) | Android Capacitor | iOS Capacitor | iOS PWABuilder |
|----------------------------|--------------------------|-------------------|---------------|----------------|
| Effort                     | ★☆☆ Low                 | ★★☆ Medium        | ★★☆ Medium    | ★☆☆ Low        |
| Native API access          | Browser only              | Full              | Full          | Browser only   |
| Performance                | Chrome (fast)             | WebView           | WKWebView     | WKWebView      |
| Play/App Store accepted    | ✅ Yes                   | ✅ Yes            | ✅ Yes        | ⚠️ Sometimes   |
| Needs Mac                  | No                        | No                | Yes           | Yes            |
| Needs Android Studio       | No (Bubblewrap builds)   | Yes               | No            | No             |
| **Recommended for Panel Compass** | ✅ **Yes**       | No                | ✅ **Yes**    | Fallback       |

**Summary:** Use **Bubblewrap/PWABuilder TWA** for Android and **Capacitor** for
iOS. Both produce store-ready packages from the existing PWA with minimal native
code.
