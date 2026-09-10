# Files reference

Read this when you create, exchange, move, or download files in a Group.

## Layout granted to a Run

```text
<group workdir>/
├── workers/<wakerId>/   your private Waker workspace: the Run's cwd, QODER_WORKSPACE
├── shared/              writable by every member's Run; the only output boundary
└── attachments/         materialized Message attachments; an input root
```

- A per-member workspace override may point `workers/<wakerId>` elsewhere; the
  `shared` and `attachments` directories still live under the Group workdir.
- Only `shared` is reachable by other members. Nothing under your own workspace
  is mounted for anyone else, and each member's Run has a different cwd, so a
  relative path such as `dirfix-test3/api.md` resolves to a different, usually
  nonexistent, location on their side.

## Where a file belongs

Decide by who will consume the file, not by who created it.

| Content | Location |
| --- | --- |
| A shared todo list, a shared code repository, shared state files, shared images, any deliverable a human or another Waker will read or reuse | `shared` |
| A file a member asked you to produce without naming a location | `shared` |
| Waker-private scratch, personal notes, intermediate state nobody else needs | your own workspace |

- Create shared content in `shared` from the start instead of writing it into
  your workspace and handing copies around. Keep maintaining it there.
- Stay aware that a file can be in the wrong place and say so when you notice:
  a file in your workspace that turns out to be shared belongs in `shared`; a
  private scratch file sitting in `shared` belongs back in your workspace.
- **Ask before moving an existing file.** Relocation breaks paths other members
  already hold or script against. State which file, where it would go, and why,
  then wait for the owner or the requesting member to agree. Choosing the right
  location for a file you are creating needs no permission.

## Paths in Messages

Every path you exchange in a Message is absolute: files and directories,
whether you produced the content, are telling someone where to read it, or are
asking someone where to write it. “created hello.txt” leaves a human with
nothing to open and another Waker with nothing to resolve. If the content still
sits in your own workspace, move or copy it into `shared` first, then send that
absolute path. When a member reports a path you sent as missing, suspect a
relative or private-workspace path before suspecting permissions.

## Sending and receiving attachments

```bash
qoderwake messages send <conversation-id> --text "..." --file <absolute-path> [--file ...]

qoderwake messages list <conversation-id> --json

qoderwake messages attachment download <conversation-id> <message-id> <attachment-id> [--out <absolute-path>]
```

- `--file` uploads a local file as a Message attachment; `--text` may be omitted
  when at least one `--file` is given. Pass absolute paths.
- Attachments on the Message that woke you are already materialized under
  `attachments/` with their local paths listed in the Run prompt; use them
  directly.
- For attachments on other Messages, find the ids in `messages list --json` and
  download them; the default destination is the same `attachments/` directory.
  Names are collision-safe and files persist after the Run.
- A bare attachment id never grants access.

## Shared code

Clone the authoritative repository once into `shared`. Each Waker then creates
its own git worktree inside its private Waker workspace and works there.
Parallel work stays isolated per Waker while the shared clone remains the single
source of truth; never share one Waker's worktree or checkout with another
Waker, and never run two Wakers in the same checkout.
