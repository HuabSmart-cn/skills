# macOS Session Join Pattern

```swift
func joinSession(sessionName: String, userName: String) async throws {
  let token = ***REDACTED***

  try videoSDK.initialize(with: initParams)
  videoSDK.delegate = self

  try videoSDK.joinSession(
    sessionName: sessionName,
    userName: userName,
    token: ***REDACTED***
  )

  try videoSDK.videoHelper.startVideo()
  try videoSDK.audioHelper.startAudio()
}
```

## Notes

- Keep media start/stop tied to session callbacks.
- Handle desktop device switching and permission denials cleanly.
