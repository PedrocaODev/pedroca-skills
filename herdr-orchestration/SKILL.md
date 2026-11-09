---
name: herdr-orchestration
description: Coordinate multi-lane implementation across isolated Git worktrees grouped hierarchically under the repository space in Herdr's SPACES sidebar, with artifact handoffs and verification gates. Use when implementing tasks across multiple lanes, workstreams, or parallel branches in Herdr.
argument-hint: "<task-or-spec> [lane definitions...]"
---

# Herdr Multi-Lane Orchestration Skill

Coordinate parallel engineering initiatives across isolated Git worktrees grouped hierarchically under the repository space in Herdr's SPACES sidebar. This skill implements the Tier 1 multiplexing pattern: isolating file systems, compiler caches, and Git indices across parallel workstreams, while maintaining lean orchestrator context via an artifact-first handoff protocol and enforcing two-stage verification gates.

## Architectural Principles

1. **Two-Tier Agent Model**:
   - **Tier 1 (Herdr Multiplexer)**: Owns process isolation, terminal panes, Git worktree lifecycles, and agent process state (`working`, `idle`, `done`, `blocked`).
   - **Tier 2 (In-Session Subagents & Lanes)**: Worker agents operate strictly inside their dedicated worktrees, emitting structured artifacts without context bleeding.
2. **Hierarchical Worktree Spaces in Herdr SPACES Sidebar**:
   - Lanes are provisioned as native Git worktrees grouped under the target repository's Space in Herdr's SPACES sidebar.
   - In Herdr's TUI, the SPACES sidebar displays a hierarchical tree:
     ```text
     SPACES
     ▾ <repo-name> (<base-branch>)
         <lane-1> (<lane-1-branch>)
         <lane-2> (<lane-2-branch>)
         <lane-3> (<lane-3-branch>)
     ```
   - Each lane gets dedicated workspace isolation (independent terminal layout, panes, and working directory) while maintaining clear visual hierarchy under the parent repository space.
3. **Artifact-First Two-Way Handoff**:
   - The orchestrator never absorbs raw worker conversation turns or verbose build logs.
   - State is transferred via kickoff briefs (`/tmp/handoff-<session>-<lane>.md`) and completion receipts (`/tmp/handoff-<session>-<lane>-result.md`).
4. **Fail-Safe Verification Gates**:
   - **Stage 1 (Self-Verification)**: Each lane agent tests its own code inside its worktree before reporting completion. Bounded remediation (max 2 retries) handles self-healing.
   - **Stage 2 (Integration Verification)**: The orchestrator validates the combined changeset on a dedicated integration branch before delivery.

---

## Phase 0: Pre-flight Verification & Environment Checks

Before creating layout or mutating Git state, verify that the environment and repository are in a known good state.

### 0.1 Verify Herdr Environment
Check that this process is running inside a Herdr-managed pane:

```bash
test "${HERDR_ENV:-}" = 1
```

If this check fails, test if the Herdr daemon is accessible:

```bash
herdr server status
```

If Herdr is not running or not installed, inform the user immediately and halt execution:
> "Error: Multi-lane orchestration requires an active Herdr session with HERDR_ENV=1. Please launch or attach Herdr before running this skill."

### 0.2 Discover Caller Context
Capture the orchestrator's multiplexer handles to ensure background operations do not disrupt caller focus and resolve the current workspace:

```bash
WS_ID="${HERDR_WORKSPACE_ID:-$(herdr workspace list | jq -r '.result.workspaces[] | select(.focused == true) | .workspace_id')}"
ORCH_WS="$WS_ID"
ORCH_TAB="${HERDR_TAB_ID:-}"
ORCH_PANE="${HERDR_PANE_ID:-}"
printf 'Caller Context: ws=%s tab=%s pane=%s\n' "$ORCH_WS" "$ORCH_TAB" "$ORCH_PANE"
```

### 0.3 Verify Clean Git State
Ensure the repository has no uncommitted changes or active rebase/merge operations:

```bash
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || { echo "Not in a git repo"; exit 1; }

REPO_ROOT=$(git rev-parse --show-toplevel)
REPO_NAME=$(basename "$REPO_ROOT")

# Ensure working directory is clean
if [ -n "$(git status --porcelain)" ]; then
  echo "Error: Uncommitted changes detected in repository. Working directory must be clean before setting up worktrees."
  git status --short
  exit 1
fi

# Resolve repository workspace ID if existing in Herdr
REPO_WS_ID=$(herdr workspace list | jq -r --arg root "$REPO_ROOT" '.result.workspaces[] | select(.worktree.repo_root == $root or .worktree.checkout_path == $root) | .workspace_id' | head -n 1)
[ -z "$REPO_WS_ID" ] && REPO_WS_ID="$ORCH_WS"
```

### 0.4 Resolve Base Branch & Session Identifiers
Determine the base branch to root all lane branches from:

```bash
BASE_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "$BASE_BRANCH" = "HEAD" ]; then
  BASE_BRANCH=$(git describe --tags --always)
fi

SESSION_ID=$(date +%s)
# Extract topic from argument or default to timestamped task
TOPIC_INPUT="${1:-multi-lane}"
TOPIC=$(echo "$TOPIC_INPUT" | tr '[:upper:]' '[:lower:]' | tr -cs 'a-z0-9' '-' | sed 's/^-//;s/-$//' | cut -c1-24)
[ -z "$TOPIC" ] && TOPIC="task-${SESSION_ID}"

echo "Initialized Orchestration Session: topic=${TOPIC} session=${SESSION_ID} base=${BASE_BRANCH} repo=${REPO_NAME}"
```

---

## Phase 1: Task Decomposition & Lane DAG Planning

Decompose the feature or specification into discrete, parallelizable workstreams structured as a Directed Acyclic Graph (DAG).

### 1.1 Dual-Mode Lane Planning

Operate in one of two modes:

#### Mode A: User-Specified Lanes
If the user provided explicit lane names or definitions in the prompt or arguments:
- Parse user-provided lanes (e.g., `backend`, `frontend`, `contracts`, `docs`).
- Map each lane to its bounded responsibility and file paths.
- Establish dependency ordering between lanes.

#### Mode B: Automatic Interactive Decomposition
If the user supplied an objective, plan, or spec without lane definitions:
1. Analyze the target specification or requirement.
2. Group tasks by architectural layers and file boundaries:
   - Shared models / database schemas / contracts
   - Core domain logic / backend services
   - Client applications / UI components
   - Integration tests / documentation
3. Construct the dependency DAG:
   - Independent tasks are scheduled in Phase 1.
   - Tasks requiring interfaces or models from Phase 1 are scheduled in Phase 2.
   - Consumers of multiple services are scheduled in Phase 3.
4. **Interactive Confirmation**: Present the proposed DAG, lane names, file boundaries, and execution phases to the user for confirmation before proceeding.

### 1.2 DAG Data Schema
Represent the plan in memory or in `/tmp/dag-${SESSION_ID}.json`. The schema corresponds directly to `LaneConfig` and `LaneType` defined in [`subagent/orchestrator.py`](subagent/orchestrator.py):

```json
{
  "topic": "feature-auth",
  "base_branch": "main",
  "phases": [
    {
      "phase": 1,
      "lanes": [
        {
          "name": "core-schema",
          "type": "implementation",
          "description": "Database migrations and token schemas",
          "paths": ["src/db/**", "src/models/**"],
          "stage1_test": "npm run test:models",
          "required_skills": ["implement", "tdd"]
        }
      ]
    },
    {
      "phase": 2,
      "lanes": [
        {
          "name": "auth-api",
          "type": "implementation",
          "description": "Authentication endpoints and JWT middleware",
          "paths": ["src/api/auth/**", "src/middleware/**"],
          "dependencies": ["core-schema"],
          "stage1_test": "npm run test:auth",
          "required_skills": ["implement", "tdd"]
        },
        {
          "name": "client-ui",
          "type": "implementation",
          "description": "Login/registration UI forms and state store",
          "paths": ["src/client/**"],
          "dependencies": ["core-schema"],
          "stage1_test": "npm run test:client",
          "required_skills": ["implement", "tdd"]
        },
        {
          "name": "api-docs",
          "type": "docs",
          "description": "API documentation and schema reference",
          "paths": ["docs/api/**"],
          "dependencies": ["auth-api"],
          "stage1_test": "",
          "required_skills": ["writing-for-agents"]
        }
      ]
    }
  ]
}
```

Lane fields (matching `LaneConfig` in [`subagent/orchestrator.py`](subagent/orchestrator.py)):
- `name`: Unique identifier for the lane.
- `type`: Workstream classification — one of `implementation`, `docs`, `research`, or `chore` (`LaneType`). Implementation lanes (where `LaneOrchestrator.is_implementation_lane(lane)` evaluates to true: `lane_type == LaneType.IMPLEMENTATION` or `"implement"` in `required_skills`) mandate `/implement` workflow enforcement, TDD, code review, and receipt gate validation.
- `description`: Bounded responsibility and deliverable.
- `paths`: Strictly bounded file paths/patterns the lane is authorized to mutate.
- `dependencies`: Prerequisite lane names whose receipts must be provided.
- `stage1_test`: Self-verification test command run inside the worktree before declaring completion.
- `required_skills`: Project skills required for the lane.

---

## Phase 2: Native Worktree Workspace Setup in SPACES Sidebar

Provision an isolated Git worktree workspace for each lane, hierarchically grouped under the repository's Space in Herdr's SPACES sidebar.

### 2.1 Visual Hierarchy in SPACES Sidebar
Lanes are provisioned as native Git worktrees grouped under the target repository's Space in Herdr's SPACES sidebar. In Herdr's TUI, the SPACES sidebar displays a hierarchical tree:

```text
SPACES
▾ <repo-name> (<base-branch>)
    <lane-1> (<lane-1-branch>)
    <lane-2> (<lane-2-branch>)
    <lane-3> (<lane-3-branch>)
```

Each lane operates in a fully isolated workspace with its own root pane, terminal layout, and independent Git index, while remaining visually organized as an indented child under the parent repository space.

### 2.2 Provision Worktrees and Launch Lane Agents
Use `herdr worktree create` with `--cwd "$REPO_ROOT"` (or `--workspace "$REPO_WS_ID"`), `--branch "$LANE_BRANCH"`, `--base "$BASE_BRANCH"`, `--label "$LANE"`, `--no-focus`, and `--trust-repository`.

For each lane declared in the DAG:

```bash
# Track created lane workspace IDs for teardown
declare -a LANE_WS_IDS=()

# For each lane:
LANE="core-schema" # Example lane
LANE_BRANCH="lane/${TOPIC}-${LANE}"

# 1. Create native Git worktree workspace grouped under the repository space
CREATE_RESP=$(herdr worktree create \
  --cwd "$REPO_ROOT" \
  --branch "$LANE_BRANCH" \
  --base "$BASE_BRANCH" \
  --label "$LANE" \
  --no-focus \
  --trust-repository)

# 2. Resolve/track LANE_WS_ID, PANE_ID, and WORKTREE_DIR from the JSON response
LANE_WS_ID=$(echo "$CREATE_RESP" | jq -r '.result.workspace.workspace_id')
PANE_ID=$(echo "$CREATE_RESP" | jq -r '.result.root_pane.pane_id')
WORKTREE_DIR=$(echo "$CREATE_RESP" | jq -r '.result.worktree.path // .result.workspace.worktree.checkout_path')

LANE_WS_IDS+=("$LANE_WS_ID")
printf 'Lane %s provisioned: ws=%s pane=%s dir=%s\n' "$LANE" "$LANE_WS_ID" "$PANE_ID" "$WORKTREE_DIR"

# 3. Start Antigravity agent in the worktree workspace's root pane
herdr agent start "$LANE" --kind agy --pane "$PANE_ID"

# 4. Handle project trust prompt if blocked (defensive fallback; workspace trust is handled automatically on startup by the `agy` wrapper)
AGENT_STATE=$(herdr agent get "$LANE" | jq -r '.result.agent.state')
if [ "$AGENT_STATE" = "blocked" ]; then
  herdr pane send-keys "$PANE_ID" Enter
fi

# 5. Wait for readiness
herdr agent wait "$LANE" --until idle --timeout 30000
```

Repeat for every lane in the initiative. Record the mapping of `lane` -> `{lane_ws_id, pane_id, worktree_dir, branch}`.

---

## Phase 3: Phased Batch Execution & Handoff Protocol

Execute lanes phase-by-phase according to the topological DAG. All lanes within a single phase run concurrently in parallel.

### 3.1 Write Kickoff Handoff Artifact
Before dispatching a lane, serialize its task brief to `/tmp/handoff-${SESSION_ID}-${LANE}.md` adhering to `LaneOrchestrator.build_lane_brief` in [`subagent/orchestrator.py`](subagent/orchestrator.py):

```markdown
# Lane Kickoff Brief: <LANE>

- **Session**: <SESSION_ID>
- **Topic**: <TOPIC>
- **Lane**: <LANE>
- **Worktree**: <WORKTREE_DIR>
- **Branch**: <LANE_BRANCH>
- **Base**: <BASE_BRANCH>

## Objective
<LANE_DESCRIPTION>

## Scope & File Boundaries
Strictly restrict file additions, edits, and deletions to:
<ALLOWED_PATHS>
Do not modify files outside this designated scope.

## Upstream Contracts & Dependencies
<IF_DEPENDENCIES_EXIST>
Read outputs from prerequisite lanes:
- Predecessor receipt: `/tmp/handoff-<SESSION_ID>-<PREDECESSOR>-result.md`
<ELSE>
None (Root Phase Lane)
</IF_DEPENDENCIES_EXIST>

<IF_IMPLEMENTATION_LANE>
## Required Skills & Workflow
- Mandatory workflow: You MUST execute `/implement` for this implementation lane (skills: `implement`, `tdd`, `code-review`).
- Enforce test-driven development (TDD), verification planning, and code review.
- You MUST declare `WORKFLOW: /implement` in your completion receipt.
<ELSE>
## Required Skills
- Apply skills appropriate for <LANE_TYPE> (e.g., `writing-for-agents`, `research`).
</IF_IMPLEMENTATION_LANE>

## Stage 1 Verification Criteria
Before declaring completion, run and pass within this worktree:
```bash
<STAGE_1_TEST_COMMAND>
```

## Completion Protocol
1. Commit all completed work to branch `<LANE_BRANCH>`.
2. Write a completion receipt to `/tmp/handoff-<SESSION_ID>-<LANE>-result.md` adhering to the required schema:
   - `VERDICT`: `PASSED` or `FAILED`
   - `WORKFLOW`: Declared workflow executed (mandatory `WORKFLOW: /implement` for implementation lanes)
   - `COMMITS`: List of commit hashes created
   - `FILES_MODIFIED`: List of modified file paths
   - `STAGE_1_VERIFICATION`: Exact test commands executed and output summary
   - `EXPORTED_CONTRACTS`: APIs, types, or interfaces produced for downstream lanes
3. Reply to notify completion.
```

### 3.2 Dispatch Lane Prompts in Parallel
Submit work prompts to all lanes in the active phase simultaneously adhering to `LaneOrchestrator.build_lane_prompt` in [`subagent/orchestrator.py`](subagent/orchestrator.py). Implementation lanes (`type == "implementation"` or `"implement"` in `required_skills`) are conditionally prefixed with `/implement `:

```bash
# Conditionally prefix with /implement for implementation lanes
if [ "$LANE_TYPE" = "implementation" ] || echo "$REQUIRED_SKILLS" | grep -qw "implement"; then
  PROMPT="/implement Execute the task specified in /tmp/handoff-${SESSION_ID}-${LANE}.md. Read the kickoff brief, strictly adhere to the /implement workflow (TDD, regular typechecking, and pre-commit code review), implement changes within your assigned file boundaries, execute Stage 1 self-verification, commit your work to branch $(git rev-parse --abbrev-ref HEAD), and write the completion receipt to /tmp/handoff-${SESSION_ID}-${LANE}-result.md. Reply when complete."
else
  PROMPT="Execute the task specified in /tmp/handoff-${SESSION_ID}-${LANE}.md. Read the kickoff brief, execute changes within your assigned file boundaries, execute Stage 1 self-verification, commit your work to branch $(git rev-parse --abbrev-ref HEAD), and write the completion receipt to /tmp/handoff-${SESSION_ID}-${LANE}-result.md. Reply when complete."
fi

herdr agent prompt "$LANE" "$PROMPT" --wait --timeout 600000 &
```

### 3.3 Event-Driven Lifecycle Monitoring & Blocked State Trapping
Track active lane agents using the event-driven status watcher [`subagent/watcher.py`](subagent/watcher.py) combined with Antigravity's background task reactive wakeup. This replaces manual polling loops with real-time socket events (`pane.agent_status_changed`).

#### 1. Launch Event Watcher Background Task
Locate the portable skill directory and spawn `subagent/watcher.py` via `run_command` with `WaitMsBeforeAsync=500` watching all active phase lanes:

```bash
# Locate self-contained skill directory (supports skills.sh installs in local .agents/skills or ~/.gemini/skills)
SKILL_DIR="${HERDR_ORCHESTRATION_DIR:-$(find "${PWD}" ~/.gemini/skills ~/.agents/skills -maxdepth 3 -type d -name "herdr-orchestration" 2>/dev/null | head -n 1)}"
python3 "${SKILL_DIR}/subagent/watcher.py" \
  --lanes "${ACTIVE_LANES[@]}" \
  --until idle,done,blocked \
  --timeout 600
```

#### 2. Yield Turn for Reactive Wakeup
Launching `run_command` with `WaitMsBeforeAsync=500` starts the watcher command and transitions it to an asynchronous background task once 500ms elapses.

End your turn immediately after launching the watcher task (call no more tools). Antigravity automatically yields execution and resumes the orchestrator turn via Reactive Wakeup when the background watcher task exits or emits its completion notification message. Never use timers or manual polling loops (`herdr agent list`, `sleep`, or `cron`) while waiting for lane transitions.

#### 3. Parse Match Result
Inspect the JSON payload returned by the watcher on task completion:

```json
{
  "matched": true,
  "lane": "<lane>",
  "pane_id": "<pane_id>",
  "status": "idle|done|blocked",
  "reason": "event_received|already_settled",
  "data": { ... }
}
```

#### 4. Route Execution Branch by Status
- **Status `idle` or `done`**: The lane agent completed its work. Proceed immediately to Phase 3.4 (Read Completion Receipt).
- **Status `blocked`**: The lane agent stopped at an interactive dialog, permission approval, or user prompt. Trap the blocked state and alert the human user immediately:

```markdown
> [!IMPORTANT]
> **Action Required: Agent Blocked in Lane `<LANE>`**
> - **Repository**: `<REPO_NAME>`
> - **Workspace**: `<LANE_WS_ID>` (indented under `<REPO_NAME>` in SPACES sidebar)
> - **Pane**: `<PANE_ID>`
> 
> **Detected Prompt**:
> ```text
> $(herdr agent read "$LANE" --source detection --lines 20)
> ```
> Please switch to workspace `<LANE>` under `<REPO_NAME>` in Herdr's SPACES sidebar to answer the prompt or grant permission.
```

Halt automated progression on this lane until the user resolves the interaction and the agent returns to `working`, `idle`, or `done`.

### 3.4 Read Completion Receipt
When the agent reaches `idle` or `done`, inspect the receipt file:

```bash
RECEIPT_FILE="/tmp/handoff-${SESSION_ID}-${LANE}-result.md"
if [ ! -f "$RECEIPT_FILE" ]; then
  echo "Error: Receipt file $RECEIPT_FILE not found for lane $LANE"
fi
```

Validate the receipt contents against the verification rules defined in `LaneOrchestrator.verify_lane_receipt` in [`subagent/orchestrator.py`](subagent/orchestrator.py):
- Extract `VERDICT` (must match `PASSED`).
- **Enforce Implementation Workflow Gate**: For implementation lanes (`type: "implementation"` or `"implement"` in `required_skills`), inspect the `WORKFLOW` field:
  - Must be present and declare an implementation workflow containing `implement` (case-insensitive, e.g. `WORKFLOW: /implement` or `WORKFLOW: implement`).
  - If missing or does not contain `implement`, reject Stage 1 verification:
    `"Stage 1 rejected: implementation lane did not execute /implement workflow"`.
  - Non-implementation lanes (`docs`, `research`, `chore` without `implement` skill) pass on `VERDICT: PASSED` without requiring `WORKFLOW: implement`.
- Extract list of commits created (`git -C "$WORKTREE_DIR" log --oneline "$BASE_BRANCH..$LANE_BRANCH"`).
- Extract modified files list.

### 3.5 Bounded Retries on Stage 1 Failure
If `VERDICT` is `FAILED` or Stage 1 verification failed:
- **Maximum Retries**: Up to 2 fix attempts per lane.
- Send remediation prompt:
  ```bash
  herdr agent prompt "$LANE" "Stage 1 verification failed. Review test failures and fix the code: <failure_diagnostic>. Re-run Stage 1 verification and update /tmp/handoff-${SESSION_ID}-${LANE}-result.md." --wait --timeout 300000
  ```
- If a lane fails after 2 fix attempts:
  - Mark the lane as permanently failed.
  - Halt all downstream phases that depend on this lane.
  - Report the failure to the user with the worktree path and logs for manual diagnosis.

### 3.6 Phase Synchronization Barrier
Ensure **all** lanes in Phase $N$ report `VERDICT: PASSED` before launching any lanes in Phase $N+1$.

---

## Phase 4: Integration Delivery & Stage 2 Verification

Once all DAG phases have completed successfully, consolidate the changes onto a dedicated integration branch and run comprehensive verification.

### 4.1 Create Integration Branch
In the primary repository working directory:

```bash
INTEGRATION_TIMESTAMP=$(date +%Y%m%d%H%M%S)
INTEGRATION_BRANCH="integrate/${TOPIC}-${INTEGRATION_TIMESTAMP}"

git checkout -b "$INTEGRATION_BRANCH" "$BASE_BRANCH"
```

### 4.2 Sequential Lane Merging
Merge each lane branch in topological order using non-fast-forward merges to preserve provenance:

```bash
for LANE in "${ORDERED_LANES[@]}"; do
  LANE_BRANCH="lane/${TOPIC}-${LANE}"
  echo "Merging lane ${LANE} (${LANE_BRANCH}) into ${INTEGRATION_BRANCH}..."
  
  if ! git merge --no-ff "$LANE_BRANCH" -m "Merge lane '${LANE}' into ${INTEGRATION_BRANCH}"; then
    echo "Conflict detected merging ${LANE_BRANCH}!"
    # Inspect conflicted files
    CONFLICTS=$(git diff --name-only --diff-filter=U)
    echo "Conflicted files: $CONFLICTS"
    
    # If conflicts can be cleanly resolved using contract definitions, resolve them.
    # Otherwise, halt and prompt the user for interactive resolution.
    exit 1
  fi
done
```

### 4.3 Stage 2 Integration Verification
Execute the project's top-level integration test suite across the combined working tree:

```bash
# Example verification suite:
npm run lint
npm run typecheck
npm run test:integration
npm test
```

- If Stage 2 passes: Integration is complete and verified.
- If Stage 2 fails: Inspect the regression, identify the conflicting lane contracts, and apply a targeted fix commit on the integration branch.

---

## Phase 5: Review & Interactive Teardown

Present the outcome to the developer and prompt before pruning temporary infrastructure.

### 5.1 Review Presentation
Display a comprehensive summary:

```markdown
## Multi-Lane Orchestration Summary

- **Topic**: `<TOPIC>`
- **Integration Branch**: [`integrate/<TOPIC>-<TS>`](file:///path/to/repo)
- **Base Branch**: `<BASE_BRANCH>`
- **Total Commits**: `<COUNT>`
- **Verification**: Stage 1 (Passed across all lanes), Stage 2 (Passed on integration branch)

### Executed Lanes
| Lane | Branch | Worktree Space | Worktree Directory | Stage 1 Verdict | Commits |
|---|---|---|---|---|---|
| `core-schema` | `lane/<topic>-core-schema` | `<LANE_WS_ID>` | `~/.herdr/worktrees/<repo>/<branch>` | PASSED | 2 |
| `auth-api` | `lane/<topic>-auth-api` | `<LANE_WS_ID>` | `~/.herdr/worktrees/<repo>/<branch>` | PASSED | 3 |
| `client-ui` | `lane/<topic>-client-ui` | `<LANE_WS_ID>` | `~/.herdr/worktrees/<repo>/<branch>` | PASSED | 4 |

### Files Modified
<LIST_OF_ALL_TOUCHED_FILES>
```

### 5.2 Interactive Teardown Prompt
Explicitly prompt the user before cleaning up:

```text
Would you like to remove the child worktree workspaces and delete temporary lane branches? [y/N]:
```

### 5.3 Conditional Teardown Execution
- **If user approves (`y` / `yes`)**:
  ```bash
  # 1. Remove each child worktree workspace (removes child rows from SPACES sidebar and cleans up worktrees from disk)
  for LANE_WS in "${LANE_WS_IDS[@]}"; do
    herdr worktree remove --workspace "$LANE_WS" --force
  done

  # 2. Delete temporary lane branches
  for LANE in "${ORDERED_LANES[@]}"; do
    git branch -D "lane/${TOPIC}-${LANE}"
  done

  # 3. Prune git worktree records
  git worktree prune

  # 4. Remove temporary handoff files
  rm -f /tmp/handoff-${SESSION_ID}-*

  echo "Cleaned up all child worktree workspaces, lane branches, and temporary handoffs. Caller workspace and parent repository space preserved."
  ```

- **If user declines (`n` / `no` / inspect)**:
  ```text
  Teardown bypassed. All worktrees, lane branches, and child workspaces remain preserved in the SPACES sidebar for manual inspection.
  - Parent Repository Space: <REPO_NAME>
  - Child Worktree Spaces: <LANE_WS_IDS>
  - Worktrees: ~/.herdr/worktrees/<repo>/
  ```

---

## Safety & Coordination Rules

- **Strict Boundary Enforcement**: Always specify allowed file path boundaries in each lane's kickoff brief. Reject lane changes outside assigned paths.
- **Never Force Push**: Never run `git push --force` or modify remote branches without explicit user instructions.
- **Preserve User Focus**: Pass `--no-focus` when creating worktree workspaces or panes so the user's active cursor is not hijacked.
- **Clean Handshake**: Always verify `/tmp/handoff-...-result.md` existence and parse `VERDICT` before advancing to dependent DAG phases.
- **Safe Workspace Preservation**: On teardown, remove each child worktree workspace using `herdr worktree remove --workspace "$LANE_WS_ID" --force`, which removes the child rows from the SPACES sidebar and cleans up the worktrees from disk. Never close the caller workspace or the parent repository space. Always prompt the user before removing worktrees.
