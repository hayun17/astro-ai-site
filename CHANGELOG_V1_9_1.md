# AstroMYLA v1.9.1 — Brand Icon

This patch keeps the full v1.9 Signature Insights feature set and adds the approved AstroMYLA brand icon across browser/search/mobile surfaces.

## Added
- New lavender AstroMYLA favicon based on the approved A + crescent + orbit emblem.
- `favicon.ico`
- 48×48 and 96×96 PNG favicons.
- 180×180 Apple touch icon.
- 192×192 and 512×512 app icons.
- Web app manifest and theme color.
- Favicon declarations in `frontend/index.html` for Google/browser discovery.

## Deployment
Use `DEPLOY_ASTROMYLA_V1_9_1.ps1`. It creates a rollback branch, runs the existing backend regression suite and frontend production build, then pushes only if all checks pass.

Google Search may keep the previous generic globe icon until the homepage is crawled again. After deployment, request indexing for `https://astromyla.com/` in Google Search Console.
