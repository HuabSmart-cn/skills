# Auth and Token Model

## Token types used by wrapper

- `jwtToken` in `initSDK`: ***REDACTED***
- `zoomAccessToken` in `startMeeting`: ***REDACTED***

## Security model

- Generate tokens server-side only.
- Never ship SDK secret in the app.
- Keep JWT short-lived and rotate aggressively.

## Flow guidance

- Participant join: `initSDK(jwtToken)` + `joinMeeting(meetingNumber, password)`
- Host start: `initSDK(jwtToken)` + `startMeeting(zoomAccessToken=ZAK, meetingNumber)`
