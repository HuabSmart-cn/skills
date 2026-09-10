---
name: deploy
description: >
  Deploy static websites to GitHub Pages.
  Use when the user asks to deploy, publish, host, or put a website online.
  Also use when the user clicks the "Deploy to GitHub Pages" action button after creating an HTML page.
metadata:
  category: system
  icon: githubpages
---

# Website Deployment

Deploy static websites (HTML, CSS, JS, images) to GitHub Pages using its HTTP API. No CLI tools required — only `curl`.

> [!CAUTION]
> This is a **write** operation that publishes content to the public internet. Always confirm with the user before deploying.

## Supported Platforms

| Platform | Auth | Result URL |
|---|---|---|
| GitHub Pages | `gh` CLI token / OAuth / PAT | `https:***REDACTED***

## Credential Storage

Store tokens in `~/.cola/deploy/`:

***REDACTED***
mkdir -p ~/.cola/deploy
echo "TOKEN_VALUE" > ~/.cola/deploy/github_token
chmod 600 ~/.cola/deploy/*
```

Read tokens:

***REDACTED***
GH_TOKEN=***REDACTED***
```

## Setup (One-Time)

### GitHub Pages

**Option 1: Local `gh` CLI token (highest priority)**

Before prompting the user, check if the GitHub CLI is installed and already authenticated:

```bash
gh auth token 2>/dev/null
```

If this returns a token, use it directly:

***REDACTED***
GH_TOKEN=***REDACTED***
```

Verify the token is valid and has the `repo` scope required for GitHub Pages deployment:

***REDACTED***
curl -si "https://api.github.com/user" \
  -H "Authorization: ***REDACTED***
  -H "Accept: application/vnd.github+json" 2>/dev/null
```

Check the response:
1. The body must include a `login` field (token is valid).
2. The `x-oauth-scopes` response header must contain the `repo` scope. Without `repo`, the token cannot create repos or manage GitHub Pages.

If both checks pass, save the token and skip to deployment:

***REDACTED***
mkdir -p ~/.cola/deploy
echo "$GH_TOKEN" > ~/.cola/deploy/github_token
chmod 600 ~/.cola/deploy/github_token
```

If `gh` is not installed, not authenticated, or the token lacks the `repo` scope, tell the user their `gh` token doesn't have permission to deploy to GitHub Pages, then fall through to Option 2.

**Option 2: OAuth (requires Cola to be logged in)**

If no token is found at `~/.cola/deploy/github_token`, ask the user:
***REDACTED***

If the user agrees, open the authorization URL:

***REDACTED***
open "https://api.colaos.ai/v1/auth/github/start"
```

The flow uses a claim-code pattern and needs the Cola desktop app to finish the exchange:

1. Browser → `GET /v1/auth/github/start` → redirects to GitHub OAuth (scope: `repo`)
2. GitHub → `GET /v1/auth/github/callback?code=...` → cloud backend exchanges code for a GitHub token, stashes `{access_token, github_user}` in Redis under a one-use claim code (5-min TTL), then redirects to `colaos://github/callback?claim_code=...`
3. Electron's deep-link handler catches the `colaos://` URL → `POST /v1/auth/github/claim { claim_code }` with the user's Cola Bearer auth → cloud returns `{access_token, github_user}` → Electron writes the token to `~/.cola/deploy/github_token` (mode `0600`)

The `/claim` step is gated by `requireAuth`, so the user must already be signed in to Cola. If they're not, the claim fails and no token file is written.

Poll for the token file to confirm the round-trip completed:

***REDACTED***
for i in $(seq 1 30); do
  if [ -f ~/.cola/deploy/github_token ]; then
    echo "GitHub token received"
    break
  fi
  sleep 2
done
```

If the file never appears, the user likely isn't logged in to Cola or dismissed the browser — fall back to Option 3.

**Option 3: Manual PAT**

If OAuth is unavailable or the user prefers a personal access token:

***REDACTED***
2. Select the **repo** scope
3. Generate and copy the token
4. Save it:

```bash
mkdir -p ~/.cola/deploy
echo "TOKEN_VALUE" > ~/.cola/deploy/github_token
chmod 600 ~/.cola/deploy/github_token
```

Verify:

```bash
curl -s "https://api.github.com/user" \
  -H "Authorization: ***REDACTED***
  -H "Accept: application/vnd.github+json" | cat
```

## Deploying to GitHub Pages

### Repository and Page Path Strategy

Use one shared public repository for all Cola GitHub Pages deployments:

```bash
REPO_NAME="cola-pages"
```

Deploy each website into its own directory on the `gh-pages` branch:

```bash
PAGE_SLUG="my-page"
PAGE_DIR="$PAGE_SLUG"
PAGE_PREFIX="$PAGE_DIR/"
PAGE_URL="https://$GH_USER.github.io/$REPO_NAME/$PAGE_SLUG/"
```

Choose a short lowercase kebab-case `PAGE_SLUG` from the page title or purpose. If updating a page the user has already deployed, reuse the same slug and overwrite only that directory. If deploying a new page, create a new slug. Do not create a new repository unless the user explicitly asks for one.

When building repository paths, concatenate with `PAGE_PREFIX` without adding another slash: `${PAGE_PREFIX}assets/logo.png`, not `$PAGE_PREFIX/assets/logo.png`.

### GitHub Pages Path Warning

GitHub Pages serves each deployed Cola page at `https://{user}.github.io/cola-pages/{page-slug}/` — a nested subdirectory, not the domain root. Absolute paths like `/style.css` would resolve to `https://{user}.github.io/style.css` instead of the correct `https://{user}.github.io/cola-pages/{page-slug}/style.css`.

**Before deploying to GitHub Pages, you MUST check and fix absolute paths in the source files:**

1. Read HTML files — look for `src="/..."`, `href="/..."` attributes referencing local assets
2. Read CSS files — look for `url(/...)` references to local assets
3. Read JS files — look for fetch/import paths referencing local assets
4. Convert local absolute paths to paths relative to the file that references them: `/style.css` → `./style.css`, `/assets/logo.png` → `./assets/logo.png`
5. For nested files, preserve the correct relative depth: `pages/about.html` referencing `/assets/logo.png` should use `../assets/logo.png`
6. Do NOT change: external URLs (`https://...`), protocol-relative URLs (`//cdn...`), API endpoints, data/blob URLs, mailto/tel links, or anchor links (`#...`)

After rewriting paths, the page must work when served from `/$REPO_NAME/$PAGE_SLUG/`, not just from `/`.

### Step 1: Get Username

```bash
GH_USER=$(curl -s "https://api.github.com/user" \
  -H "Authorization: ***REDACTED***
  -H "Accept: application/vnd.github+json" | grep -o '"login" *: *"[^"]*"' | cut -d'"' -f4)
```

### Step 2: Create Shared Repo (422 = already exists)

```bash
REPO_NAME="cola-pages"

curl -s -X POST "https://api.github.com/user/repos" \
  -H "Authorization: ***REDACTED***
  -H "Accept: application/vnd.github+json" \
  -H "Content-Type: application/json" \
  -d "{\"name\": \"$REPO_NAME\", \"auto_init\": false, \"private\": false}" | cat
```

### Step 3: Choose Page Slug

```bash
PAGE_SLUG="my-page"
PAGE_DIR="$PAGE_SLUG"
PAGE_PREFIX="$PAGE_DIR/"
PAGE_URL="https://$GH_USER.github.io/$REPO_NAME/$PAGE_SLUG/"
```

Use a unique slug for a new page. Reuse the existing slug when the user asks to update a previously deployed page.

### Step 4: Read Current gh-pages Ref (if any)

Check if the shared repo already has a `gh-pages` branch:

```bash
REF_JSON=$(curl -s "https://api.github.com/repos/$GH_USER/$REPO_NAME/git/ref/heads/gh-pages" \
  -H "Authorization: ***REDACTED***
  -H "Accept: application/vnd.github+json")

PARENT_SHA=$(printf '%s' "$REF_JSON" | grep -o '"sha" *: *"[^"]*"' | head -1 | cut -d'"' -f4)
BASE_TREE_SHA=""
EXISTING_PAGE_PATHS=""

if [ -n "$PARENT_SHA" ]; then
  COMMIT_JSON=$(curl -s "https://api.github.com/repos/$GH_USER/$REPO_NAME/git/commits/$PARENT_SHA" \
    -H "Authorization: ***REDACTED***
    -H "Accept: application/vnd.github+json")
  BASE_TREE_SHA=$(printf '%s\n' "$COMMIT_JSON" | awk '
    /"tree"[[:space:]]*:[[:space:]]*\{/ { in_tree = 1; next }
    in_tree && /"sha"[[:space:]]*:/ {
      value = $0
      sub(/^.*"sha"[[:space:]]*:[[:space:]]*"/, "", value)
      sub(/".*$/, "", value)
      print value
      exit
    }
    in_tree && /\}/ { in_tree = 0 }
  ')

  if [ -z "$BASE_TREE_SHA" ]; then
    echo "Could not read the existing gh-pages tree SHA. Stop instead of risking deletion of previously deployed pages."
    exit 1
  fi

  EXISTING_TREE_JSON=$(curl -s "https://api.github.com/repos/$GH_USER/$REPO_NAME/git/trees/$BASE_TREE_SHA?recursive=1" \
    -H "Authorization: ***REDACTED***
    -H "Accept: application/vnd.github+json")
  EXISTING_PAGE_PATHS=$(printf '%s\n' "$EXISTING_TREE_JSON" | awk -v prefix="$PAGE_PREFIX" '
    /"path"[[:space:]]*:/ {
      entry_path = $0
      sub(/^.*"path"[[:space:]]*:[[:space:]]*"/, "", entry_path)
      sub(/".*$/, "", entry_path)
      next
    }
    /"type"[[:space:]]*:[[:space:]]*"blob"/ && entry_path ~ ("^" prefix) {
      print entry_path
    }
    /\}/ { entry_path = "" }
  ')
fi
```

If `PARENT_SHA` is set, use it as the parent commit in Step 7. If `BASE_TREE_SHA` is set, use it as `base_tree` in Step 6. This preserves every previously deployed page in the shared repository. If `PARENT_SHA` exists but `BASE_TREE_SHA` cannot be read, stop and report the error instead of deploying.

`EXISTING_PAGE_PATHS` lists files currently published under the target page directory. Use it in Step 6 to delete stale files when reusing a slug.

### Step 5: Create Blobs (one per file)

```bash
NEW_PAGE_PATHS_FILE=$(mktemp)

UPLOAD_PATH="${PAGE_PREFIX}index.html"
printf '%s\n' "$UPLOAD_PATH" >> "$NEW_PAGE_PATHS_FILE"
CONTENT_B64=$(base64 -i "/path/to/file")
curl -s -X POST "https://api.github.com/repos/$GH_USER/$REPO_NAME/git/blobs" \
  -H "Authorization: ***REDACTED***
  -H "Accept: application/vnd.github+json" \
  -H "Content-Type: application/json" \
  -d "{\"content\": \"$CONTENT_B64\", \"encoding\": \"base64\"}" | cat
```

Save the `sha` from each response for the Step 6 tree entries, and write every new repository path to `$NEW_PAGE_PATHS_FILE`. Use paths like `${PAGE_PREFIX}index.html` and `${PAGE_PREFIX}assets/logo.png`; do not insert an extra slash after `$PAGE_PREFIX`.

### Step 6: Create Tree

```bash
curl -s -X POST "https://api.github.com/repos/$GH_USER/$REPO_NAME/git/trees" \
  -H "Authorization: ***REDACTED***
  -H "Accept: application/vnd.github+json" \
  -H "Content-Type: application/json" \
  -d '{
    "base_tree": "BASE_TREE_SHA_IF_PRESENT",
    "tree": [
      {"path": "my-page/index.html", "mode": "100644", "type": "blob", "sha": "BLOB_SHA"},
      {"path": "my-page/style.css", "mode": "100644", "type": "blob", "sha": "BLOB_SHA"}
    ]
  }' | cat
```

When `BASE_TREE_SHA` is empty, omit `base_tree` and create the first `gh-pages` tree. When `BASE_TREE_SHA` is present, include `base_tree`; otherwise this deployment will replace the whole repository contents and delete previously deployed pages.

All uploaded file paths must be under `$PAGE_PREFIX`. Example: local `assets/logo.png` becomes `${PAGE_PREFIX}assets/logo.png`. Replace `my-page` in the example JSON with the actual `$PAGE_SLUG`.

When reusing an existing slug, overwrite the whole page directory, not just the files present in the new upload. For every path in `EXISTING_PAGE_PATHS` that is not present in `$NEW_PAGE_PATHS_FILE`, add a deletion entry to the tree:

```json
{ "path": "my-page/old-image.png", "sha": null }
```

Deletion entries must be included in the same tree request as the uploaded file entries. This prevents removed or renamed assets from staying publicly reachable after an update.

### Step 7: Create Commit

```bash
curl -s -X POST "https://api.github.com/repos/$GH_USER/$REPO_NAME/git/commits" \
  -H "Authorization: ***REDACTED***
  -H "Accept: application/vnd.github+json" \
  -H "Content-Type: application/json" \
  -d '{"message": "Deploy via Cola", "tree": "TREE_SHA", "parents": []}' | cat
```

If `PARENT_SHA` is set, include it in `parents`:

```bash
curl -s -X POST "https://api.github.com/repos/$GH_USER/$REPO_NAME/git/commits" \
  -H "Authorization: ***REDACTED***
  -H "Accept: application/vnd.github+json" \
  -H "Content-Type: application/json" \
  -d '{"message": "Deploy via Cola", "tree": "TREE_SHA", "parents": ["PARENT_SHA"]}' | cat
```

### Step 8: Create or Update gh-pages Ref

Check if ref exists:

```bash
curl -s "https://api.github.com/repos/$GH_USER/$REPO_NAME/git/ref/heads/gh-pages" \
  -H "Authorization: ***REDACTED***
  -H "Accept: application/vnd.github+json" | cat
```

Create (first time):

```bash
curl -s -X POST "https://api.github.com/repos/$GH_USER/$REPO_NAME/git/refs" \
  -H "Authorization: ***REDACTED***
  -H "Accept: application/vnd.github+json" \
  -H "Content-Type: application/json" \
  -d '{"ref": "refs/heads/gh-pages", "sha": "COMMIT_SHA"}' | cat
```

If creating the ref fails because `gh-pages` already exists, another deployment created it concurrently. Re-run Step 4 and continue through the update path below; do not force-update over the newly created branch.

Update (subsequent deploys):

```bash
curl -s -X PATCH "https://api.github.com/repos/$GH_USER/$REPO_NAME/git/refs/heads/gh-pages" \
  -H "Authorization: ***REDACTED***
  -H "Accept: application/vnd.github+json" \
  -H "Content-Type: application/json" \
  -d '{"sha": "COMMIT_SHA", "force": false}' | cat
```

Do not use `force: true`. If this PATCH returns `409`, or the response says the update is not a fast-forward, another deployment updated `gh-pages` concurrently. Re-run Step 4 to read the latest `PARENT_SHA`, `BASE_TREE_SHA`, and `EXISTING_PAGE_PATHS`, then recreate the Step 6 tree and Step 7 commit using the same uploaded blob SHAs plus a fresh stale-file deletion list. Retry the non-forced PATCH with the new commit. Retry this read/rebuild/update loop up to 3 times, then report the conflict to the user instead of forcing the branch.

### Step 9: Enable GitHub Pages (409 = already enabled)

```bash
curl -s -X POST "https://api.github.com/repos/$GH_USER/$REPO_NAME/pages" \
  -H "Authorization: ***REDACTED***
  -H "Accept: application/vnd.github+json" \
  -H "Content-Type: application/json" \
  -d '{"build_type": "legacy", "source": {"branch": "gh-pages", "path": "/"}}' | cat
```

### Step 10: Wait for GitHub Pages to Finish

Do not tell the user the site is live immediately after Step 9. Creating or updating the `gh-pages` ref only starts GitHub Pages work; the public URL may still show a 404 or the previous version for a short time.

Poll the latest Pages build and wait for the commit deployed in Step 7:

```bash
PAGE_URL="https://$GH_USER.github.io/$REPO_NAME/$PAGE_SLUG/"
DEPLOY_STATUS="pending"

for i in $(seq 1 60); do
  BUILD_JSON=$(curl -s "https://api.github.com/repos/$GH_USER/$REPO_NAME/pages/builds/latest" \
    -H "Authorization: ***REDACTED***
    -H "Accept: application/vnd.github+json")

  BUILD_STATUS=$(printf '%s' "$BUILD_JSON" | grep -o '"status" *: *"[^"]*"' | head -1 | cut -d'"' -f4)
  BUILD_COMMIT=$(printf '%s' "$BUILD_JSON" | grep -o '"commit" *: *"[^"]*"' | head -1 | cut -d'"' -f4)
  BUILD_ERROR=$(printf '%s' "$BUILD_JSON" | grep -o '"message" *: *"[^"]*"' | head -1 | cut -d'"' -f4)

  if [ "$BUILD_COMMIT" = "COMMIT_SHA" ] && [ "$BUILD_STATUS" = "built" ]; then
    HTTP_STATUS=$(curl -L -s -o /dev/null -w "%{http_code}" "$PAGE_URL")
    if [ "$HTTP_STATUS" = "200" ]; then
      DEPLOY_STATUS="live"
      break
    fi
  fi

  if [ "$BUILD_COMMIT" = "COMMIT_SHA" ] && { [ "$BUILD_STATUS" = "errored" ] || [ "$BUILD_STATUS" = "error" ] || [ "$BUILD_STATUS" = "failed" ]; }; then
    DEPLOY_STATUS="failed"
    echo "GitHub Pages build failed: ${BUILD_ERROR:-unknown error}"
    break
  fi

  sleep 5
done

if [ "$DEPLOY_STATUS" = "live" ]; then
  echo "GitHub Pages is live: $PAGE_URL"
elif [ "$DEPLOY_STATUS" = "failed" ]; then
  echo "GitHub Pages deployment failed. Check the Pages build error above."
else
  echo "GitHub Pages deployment was submitted but is still building: $PAGE_URL"
fi
```

When replying to the user:

- If `DEPLOY_STATUS=live`, say the site is live and include `https://$GH_USER.github.io/$REPO_NAME/$PAGE_SLUG/`.
- If `DEPLOY_STATUS=failed`, say the deployment failed and include the build error if present.
- If the wait loop times out, say the deployment was submitted but GitHub Pages is still building. Include the URL, but do not claim it is already live.

## Notes

- GitHub Pages serves over HTTPS by default
- GitHub Pages requires a **public** repository on free plans
- The shared `cola-pages` repository and published Pages site should stay under GitHub Pages size limits; avoid deploying large videos, archives, dependency folders, or build caches
- Skip `.git`, `node_modules`, `.DS_Store`, `.env` when collecting files for upload
