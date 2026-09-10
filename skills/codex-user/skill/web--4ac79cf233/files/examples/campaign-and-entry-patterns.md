# Campaign and Entry Patterns

## Campaign-First Pattern (Recommended)

```html
<script data-apikey=***REDACTED***
<script>
window.addEventListener('zoomCampaignSdk:ready', () => {
  window.zoomCampaignSdk.show();
  window.zoomCampaignSdk.on('engagement_started', () => {
    console.log('engagement started');
  });
});
</script>
```

## Runtime User Context Refresh

```javascript
window.zoomCampaignSdkConfig = {
  env: 'us01',
  apikey: ***REDACTED***
  firstName: 'Ada',
  email: 'ada@example.com'
};

window.addEventListener('zoomCampaignSdk:ready', async () => {
  if (window.zoomCampaignSdk.waitForReady) {
    await window.zoomCampaignSdk.waitForReady();
  }
  window.zoomCampaignSdk.updateUserContext();
});
```

## Entry ID Fallback Pattern

Use entry ID only when your flow requires pre-chat data collection that cannot be handled in campaign configuration.
