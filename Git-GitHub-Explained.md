# Git: Key Concepts Overview

## 1. The Three Areas

Git has three local areas where your files live:

```
┌──────────────┐     git add     ┌──────────────┐    git commit    ┌──────────────┐
│              │ ──────────────> │              │ ───────────────> │              │
│  Working     │                 │   Staging    │                  │  Repository  │
│  Directory   │                 │   Area       │                  │  (.git)      │
│              │                 │              │                  │              │
│  (your files │                 │  (files you  │                  │  (permanent  │
│   on disk)   │                 │   picked to  │                  │   snapshots) │
│              │                 │   save next) │                  │              │
└──────────────┘                 └──────────────┘                  └──────────────┘
```

- **Working Directory** — the actual files you edit
- **Staging Area** — a "shopping cart" where you choose what goes into the next commit
- **Repository** — the full history of saved snapshots (commits)

---

## 2. Commits

A commit is a snapshot of your project at a point in time. Each commit points back to its parent:

```
    commit A ◄──── commit B ◄──── commit C ◄──── commit D
    "init"         "add login"    "fix bug"       "add search"
                                                       ▲
                                                       │
                                                      HEAD
```

- **HEAD** — a pointer to where you currently are in history
- Each commit has a unique hash (e.g., `a3f8b2c`) and a message

---

## 3. Branches

A branch is just a movable pointer to a commit. It lets you work on things in parallel:

```
                          ┌─── E ◄── F        ← feature branch
                          │
    A ◄── B ◄── C ◄── D                      ← main branch
                          │
                          └─── G              ← bugfix branch
```

- **main** (or master) — the default branch, usually the "source of truth"
- Creating a branch is cheap — it's just a pointer, not a copy of files

---

## 4. Merging

When your feature is done, you merge it back:

```
    BEFORE merge:                    AFTER merge:

         E ◄── F   (feature)             E ◄── F
        /                               /         \
    A ◄── B ◄── C   (main)         A ◄── B ◄── C ◄── M   (main)
                                                      │
                                                  merge commit
```

A **merge conflict** happens when both branches edited the same lines. Git asks you to choose which version to keep.

---

## 5. Remotes (GitHub/GitLab)

A remote is a copy of your repository on a server:

```
    ┌─────────────────────────────────────────────┐
    │            GitHub (remote)                   │
    │                                             │
    │    A ◄── B ◄── C          (origin/main)     │
    └──────────────────┬──────────────────────────┘
                       │
              git push │  ▲  git pull / git fetch
                       │  │
                       ▼  │
    ┌──────────────────────────────────────────────┐
    │          Your Computer (local)               │
    │                                              │
    │    A ◄── B ◄── C ◄── D    (main)            │
    └──────────────────────────────────────────────┘
```

- **`git push`** — upload your new commits to the remote
- **`git pull`** — download new commits from the remote
- **`git clone`** — copy an entire remote repo to your machine for the first time
- **origin** — the default name for the remote you cloned from

---

## 6. Pull Requests (PRs)

A pull request is **not a git feature** — it's a GitHub/GitLab feature built on top of git. It's a way to propose and review changes before merging.

Here's the workflow:

```
    Step 1: Create a branch and push it
    ─────────────────────────────────────
    main:       A ◄── B ◄── C
    feature:                  └── D ◄── E     ← you push this branch


    Step 2: Open a Pull Request on GitHub
    ─────────────────────────────────────
    ┌──────────────────────────────────────────────┐
    │  PR #42: "Add search feature"                │
    │                                              │
    │  feature → main                              │
    │                                              │
    │  Changes:  +120 lines  -15 lines             │
    │                                              │
    │  Reviewers: @teammate                        │
    │  Status: Review requested                    │
    │                                              │
    │  Comments:                                   │
    │    @teammate: "Looks good, but can you       │
    │               add error handling?"           │
    │                                              │
    │  [Approve] [Request Changes] [Merge]         │
    └──────────────────────────────────────────────┘


    Step 3: After approval, merge the PR
    ─────────────────────────────────────
    main:       A ◄── B ◄── C ◄──────── M    ← merged!
    feature:                  └── D ◄── E ┘
```

**Why PRs exist:**
- **Code review** — teammates can read and comment on your changes
- **Discussion** — talk about the approach before it's merged
- **CI/CD** — automated tests run on the PR to catch bugs
- **History** — a record of why changes were made

---

## 7. Forks

A fork is your own copy of someone else's repository on GitHub:

```
    ┌────────────────────────────────┐
    │  Original Repo (upstream)      │
    │  github.com/org/project        │
    └───────────────┬────────────────┘
                    │  Fork (GitHub makes a copy)
                    ▼
    ┌────────────────────────────────┐
    │  Your Fork (origin)            │
    │  github.com/you/project        │
    └───────────────┬────────────────┘
                    │  git clone
                    ▼
    ┌────────────────────────────────┐
    │  Your Local Machine            │
    │  ~/project                     │
    └────────────────────────────────┘
```

You make changes on your fork, then open a PR back to the original repo. This is how most open-source contribution works.

---

## 8. Worktrees

Normally, one repo = one working directory = one branch checked out at a time. A **worktree** lets you check out multiple branches simultaneously, each in its own folder.

### The Problem

You're mid-feature and a critical bug comes in:

```
    Without worktrees:
    ──────────────────
    1. git stash                 Save your half-done work
    2. git checkout main         Switch branches
    3. ... fix the bug ...       Do the fix
    4. git commit & push         Save the fix
    5. git checkout feature      Switch back
    6. git stash pop             Restore your half-done work

    Annoying! And you might forget to stash, or lose context.
```

### The Solution

Create a second working directory linked to the same repo:

```
    git worktree add ../hotfix main
```

Now you have two directories, each on a different branch, sharing the same history:

```
    ┌──────────────────────────────────────────────────────────┐
    │                   Shared .git history                     │
    │          A ◄── B ◄── C ◄── D ◄── E ◄── F               │
    └────────────────┬──────────────────────┬──────────────────┘
                     │                      │
                     ▼                      ▼
    ┌────────────────────────┐  ┌────────────────────────┐
    │  ~/project/            │  │  ~/hotfix/             │
    │                        │  │                        │
    │  Branch: feature       │  │  Branch: main          │
    │  Status: mid-work      │  │  Status: fixing bug    │
    │                        │  │                        │
    │  Your feature code     │  │  The bug fix           │
    │  is untouched here     │  │  happens here          │
    └────────────────────────┘  └────────────────────────┘
         Main worktree              Linked worktree
```

- Both directories share the **same commits, branches, and objects**
- Changes committed in one are immediately visible to the other
- No stashing, no context switching, no risk of losing work

### Key Commands

```
    git worktree add <path> <branch>    Create a new worktree
    git worktree list                   List all worktrees
    git worktree remove <path>          Remove a worktree when done
```

### Example Workflow

```
    # You're on feature branch in ~/project
    ~/project (feature) $ git worktree add ../hotfix main

    # Now fix the bug in the other directory
    ~/hotfix (main) $ ... fix bug ...
    ~/hotfix (main) $ git add . && git commit -m "fix bug"
    ~/hotfix (main) $ git push

    # Go back to your feature — everything is exactly as you left it
    ~/project (feature) $ ... continue working ...

    # Clean up when done
    ~/project (feature) $ git worktree remove ../hotfix
```

### Rules

- Each worktree must have a **different branch** checked out (no two worktrees on the same branch)
- Worktrees are lightweight — they share the `.git` data, so they don't duplicate history
- Deleting the folder isn't enough — use `git worktree remove` to clean up properly

---

## Putting It All Together

A typical workflow:

```
1.  git clone <url>                  Clone the repo
2.  git checkout -b my-feature       Create a branch
3.  ... edit files ...               Do your work
4.  git add file1.py file2.py        Stage changes
5.  git commit -m "add feature"      Save a snapshot
6.  git push -u origin my-feature    Push to remote
7.  Open a Pull Request on GitHub    Ask for review
8.  Teammates review & approve       Get feedback
9.  Merge the PR                     Changes go to main
10. git checkout main && git pull    Update your local main
```
