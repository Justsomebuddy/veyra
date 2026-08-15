# Trusted Git executable boundary

## Status and scope

`scripts/_trusted_git.py` is a private execution boundary for the two Git
queries required by maintained repository scripts:

- `git_inventory(root)` runs `ls-files -z --cached --others
  --exclude-standard` and returns the exact nonempty byte identities;
- `git_check_ignore(root, relative)` runs `check-ignore -q -- relative` and
  interprets only status 0 as ignored and status 1 as not ignored.

The only consumers are `scripts/package_smoke.py` and
`scripts/project_hygiene.py`. The helper is source-distribution payload, not a
public `veyra-core` API, and `__all__` exposes only those two operations.

## Executable admission

The resolver never consults `PATH`, a Windows registry key, or an environment
override. It considers these fixed paths in order:

- POSIX: `/usr/bin/git`, `/usr/local/bin/git`, `/opt/local/bin/git`;
- Windows: `C:\Program Files\Git\bin\git.exe`, then
  `C:\Program Files\Git\cmd\git.exe`.

On POSIX, the executable must be a nonsymlink regular executable owned by uid
0 and not writable by group or other. Every ancestor through the filesystem
root must be a nonsymlink root-owned directory not writable by group or other.
On Windows, the executable must be a regular file and neither it nor an
ancestor may carry `FILE_ATTRIBUTE_REPARSE_POINT`. The Windows policy relies
on the standard administrator-controlled Program Files ACL. It does **not**
audit or prove that ACL.

Security-relevant `lstat` identity includes device, inode, mode, uid/gid when
available, size, modification time, change time, and Windows file attributes.
The complete executable/ancestor chain is checked during resolution, checked
again immediately before process creation, and checked after every process
attempt, including OS errors and timeouts. Identity drift rejects all output.

## Process and environment boundary

Every command starts with the admitted absolute executable and then
`--no-pager -C <absolute-root> -c core.fsmonitor=false`. It uses `shell=False`,
closed stdin, captured byte stdout/stderr, and a working directory equal to the
trusted executable's parent rather than the repository. Inventory is bounded
to 30 seconds and ignore checks to 10 seconds.

The child inherits ordinary compatibility settings, including `HOME`, XDG
locations, and therefore Git's user-level global excludes used by
`--exclude-standard`. Environment names are compared case-insensitively:
`PATH`, every `GIT_*`, `LD_*`, and `DYLD_*` entry is removed. The helper adds
only `GIT_OPTIONAL_LOCKS=0` and `GIT_TERMINAL_PROMPT=0` in the removed Git
namespace. Errors and logs use fixed reason classes and counts; they do not
publish executable paths, repository paths, environment values, stderr, or
inventory content.

## Compatibility boundary

The inventory arguments and NUL-byte parsing are byte-equivalent to the
previous callers. Preserving `HOME` and XDG configuration intentionally keeps
global exclude semantics. `check-ignore` retains the existing 0/1 decision
while now treating statuses greater than 1 as an execution failure instead of
silently classifying the probe as unignored.

## Nonclaims and residual trust

This boundary is executable-path hardening, not comprehensive Git or checkout
attestation. In particular, it does not provide:

- a cryptographic hash, signature, AuthentiCode, or version attestation for
  the Git binary;
- atomic descriptor-based execution (`fexecve`) or proof that no transient
  replacement can occur between checks and process creation;
- protection from root/administrator compromise, operating-system compromise,
  a malicious admitted Git binary, or a compromised Program Files ACL;
- Windows ACL verification, registry verification, or trust in arbitrary Git
  installations outside the fixed candidates;
- a proof about every subprocess in the repository: the boundary covers only
  the two named production consumers;
- an atomic proof that the repository worktree, index, global excludes, or Git
  configuration cannot change while Git enumerates or checks paths.

The two meta-tests that inspect repository custody still invoke Git directly.
They are test-only, stay independently reviewable, and are not hidden behind a
Bandit suppression.
