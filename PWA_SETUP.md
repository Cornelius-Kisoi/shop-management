# PWA Setup Guide for EXTREME TECH

Your Django app has been configured as a Progressive Web App (PWA). Here's what's been added:

## What's New

✅ **Service Worker** - Handles offline caching and background sync
✅ **Manifest.json** - Enables home screen installation on mobile/desktop
✅ **Offline Page** - Users see a friendly page when offline
✅ **Meta Tags** - Apple and mobile browser support

## How to Install on Mobile/Desktop

### Android
1. Visit your website on Chrome
2. Tap the menu (⋮) → "Install app"
3. Tap "Install"
4. App now appears on your home screen

### iPhone/iPad
1. Open Safari and visit your site
2. Tap Share button
3. Select "Add to Home Screen"
4. Tap "Add"

### Windows/Mac (Chrome/Edge)
1. Click the install icon in the address bar
2. Click "Install"
3. App launches in standalone window

## Next Steps for Production

### 1. Create App Icons
The app expects icon files in `/static/`:
- `icon-72.png` (72×72px)
- `icon-96.png` (96×96px)
- `icon-128.png` (128×128px)
- `icon-144.png` (144×144px)
- `icon-152.png` (152×152px)
- `icon-192.png` (192×192px)
- `icon-384.png` (384×384px)
- `icon-512.png` (512×512px)

**Quick Icon Generation:**
Use a free tool like:
- [PWA Asset Generator](https://www.pwabuilder.com/imageGenerator)
- [Favicon.io](https://favicon.io/)
- [AppIcon Generator](https://www.favicon-generator.org/)

Upload your logo → Download the generated icons → Place in `/static/`

### 2. Enable HTTPS (Critical for Production)
PWA requires HTTPS. Configure in your hosting:
- Use Let's Encrypt (free SSL certificate)
- Or use AWS Certificate Manager, Google Cloud, etc.

Update `settings.py`:
```python
SECURE_SSL_REDIRECT = True  # Force HTTPS in production
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
```

### 3. Test Your PWA

**Desktop (Chrome DevTools):**
1. Open DevTools (F12)
2. Go to Application tab
3. Check Service Worker status
4. Check Manifest tab for errors

**Mobile Testing:**
- Use [ngrok](https://ngrok.com/) to expose local dev server: `ngrok http 8000`
- Open ngrok URL on phone
- Test install and offline functionality

### 4. PWA Features Already Enabled

#### Offline Support
- Caches essential pages and assets
- Service worker intercepts network requests
- Falls back to cache when offline
- Shows offline.html when needed

#### Background Sync (Optional)
- Pending sales can sync when connection restored
- Requires IndexedDB for local storage
- Uses browser's Background Sync API

#### Home Screen Shortcuts
- "Point of Sale" → Direct to POS
- "Stock" → Direct to inventory

## How It Works

```
User opens app offline
         ↓
Service Worker intercepts request
         ↓
Check cache for response
         ↓
Return cached version OR offline.html
         ↓
When online, fetch new data and update cache
```

## Offline Sales Flow (Future Enhancement)

For complete offline support with sales:

1. **Client-side:**
   - Store sales in IndexedDB
   - Show toast: "Pending sync..."
   - Request background sync

2. **Service Worker:**
   - Detects when online
   - Sends pending sales to server
   - Marks sales as synced

3. **Backend:**
   - Receives synced sales
   - Processes normally
   - Returns confirmation

## Monitoring

Check cache and service worker health:
1. DevTools → Application → Service Workers
2. DevTools → Application → Cache Storage
3. Check Console for any errors

## Common Issues

**Service Worker not updating?**
- Force refresh: `Ctrl+Shift+R` (Windows) or `Cmd+Shift+R` (Mac)
- Check DevTools → Application → Service Workers

**Icons not showing?**
- Ensure PNG files are in `/static/`
- Check manifest.json paths
- Verify filenames match exactly

**Offline page shows error?**
- Visit `/offline.html` directly in browser
- Check Console for template errors
- Ensure `offline.html` exists

## Customization

Edit these files:

**`static/manifest.json`** - Change app name, icons, colors, shortcuts
**`static/service-worker.js`** - Customize cache strategy, add more URLs
**`templates/offline.html`** - Customize offline page design
**`templates/base.html`** - Modify PWA meta tags, notifications

## Production Checklist

- [ ] HTTPS enabled
- [ ] App icons created and placed in `/static/`
- [ ] `manifest.json` paths verified
- [ ] Service worker console logs cleaned up
- [ ] Tested on real mobile devices
- [ ] Tested offline functionality
- [ ] Cache strategy reviewed
- [ ] Update notifications tested

## Support

For PWA questions:
- [MDN Web Docs - PWA](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps)
- [Google Web Dev - PWA Checklist](https://web.dev/pwa-checklist/)
- [W3C Service Worker Spec](https://www.w3.org/TR/service-workers-1/)
