# PassPort Browser Login

The launcher uses OAuth Authorization Code + PKCE, opens the system browser for authorization, and returns to the running launcher through the `bloret://` protocol. Login no longer starts a local HTTP callback server.

## PassPort Server Configuration

Register the exact callback URL for the OAuth client `BloretLauncher`:

```text
bloret://oauth/passport
```

Both the authorization request and the authorization-code exchange use this `redirect_uri`. The server must support custom URI schemes, continue validating PKCE S256, and return the original `state` from the authorization request. Example success callback:

```text
bloret://oauth/passport?code=ONE_TIME_CODE&state=ORIGINAL_STATE
```

If the user denies authorization, return `error=access_denied` with the original `state`. The callback must carry only a one-time authorization code; never put access or refresh tokens in the URL. The browser may ask the user to confirm opening Bloret Launcher; the authorization completion page can provide an "Open Bloret Launcher" button for cases where automatic navigation is blocked.

## Launcher Behavior

1. The user clicks login in the launcher. The launcher stores a temporary state and PKCE verifier, then opens the browser.
2. The user completes authorization on the PassPort website, and the browser opens the `bloret://` callback above.
3. The system launches the launcher. The second instance forwards the callback to the original instance through the existing local IPC channel.
4. The original instance validates the callback URL, state, expiry, and replay status, then exchanges the token in the background and saves the login.

The login callback takes priority over plugin protocol handling. Authorization codes are not sent to plugins, and query parameters are not written to protocol logs. If the original instance has closed or no login is pending, the callback does not create a new login state; start the login again.

Windows and Linux use the existing protocol registration logic. On macOS, the `bloret` URL scheme still needs to be declared in the app bundle's Info.plist. Server configuration and real browser launches must be tested together in the deployment environment.

The underlying coordinator still supports `callback_mode="loopback"` for callers that explicitly need a local HTTP callback.
