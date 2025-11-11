# Development Flow for Custom LiteLLM Fork

This document explains how to maintain a custom LiteLLM fork with your own provider implementation while staying synchronized with upstream updates.

## Table of Contents
- [Overview](#overview)
- [Initial Setup](#initial-setup)
- [Branch Strategy](#branch-strategy)
- [Daily Development Workflow](#daily-development-workflow)
- [Weekly/Monthly Sync Routine](#weeklymonthly-sync-routine)
- [Conflict Resolution](#conflict-resolution)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

---

## Overview

### Repository Structure
```
BerriAI/litellm (upstream)
    ↓ sync
Your Fork: main branch (clean mirror)
    ↓ rebase
Your Fork: custom-provider branch (your modifications)
    ↓ deploy
Production
```

### Key Principles
1. **`main` branch**: Clean mirror of upstream - NEVER commit custom changes here
2. **`custom-provider` branch**: Your working branch with all custom modifications
3. **Rebase strategy**: Keeps clean, linear history and makes updates easier
4. **Isolated provider code**: Minimize conflicts by keeping custom code self-contained

---

## Initial Setup

### 1. Fork the Repository
Go to https://github.com/BerriAI/litellm and click "Fork"

### 2. Clone Your Fork
```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/litellm.git
cd litellm

# Verify current remote
git remote -v
# Should show:
# origin  https://github.com/YOUR_USERNAME/litellm.git (fetch)
# origin  https://github.com/YOUR_USERNAME/litellm.git (push)
```

### 3. Add Upstream Remote
```bash
# Add the official LiteLLM repository as 'upstream'
git remote add upstream https://github.com/BerriAI/litellm.git

# Fetch from upstream
git fetch upstream

# Verify remotes
git remote -v
# Should now show:
# origin    https://github.com/YOUR_USERNAME/litellm.git (fetch)
# origin    https://github.com/YOUR_USERNAME/litellm.git (push)
# upstream  https://github.com/BerriAI/litellm.git (fetch)
# upstream  https://github.com/BerriAI/litellm.git (push)
```

**Explanation**:
- `origin`: Your fork on GitHub (where you push your changes)
- `upstream`: Official LiteLLM repo (where you pull updates from)

### 4. Create Custom Branch
```bash
# Ensure you're on main
git checkout main

# Create and switch to custom-provider branch
git checkout -b custom-provider

# Push to your fork to create remote branch
git push -u origin custom-provider
```

**Explanation**:
- `-b custom-provider`: Creates a new branch named "custom-provider"
- `-u origin custom-provider`: Sets upstream tracking so future pushes go to origin/custom-provider

---

## Branch Strategy

### Main Branch (`main`)
**Purpose**: Mirror of official LiteLLM repository

**Rules**:
- ✅ DO: Pull updates from upstream regularly
- ✅ DO: Keep it synchronized with BerriAI/litellm
- ❌ DON'T: Commit custom changes here
- ❌ DON'T: Work directly on this branch

**Why**:
- Provides clean reference point for upstream code
- Makes it easy to compare your changes: `git diff main custom-provider`
- Allows easy recreation of custom branch if needed

### Custom Provider Branch (`custom-provider`)
**Purpose**: Your working branch with all modifications

**Rules**:
- ✅ DO: Commit all your custom provider code here
- ✅ DO: Keep provider code isolated in `litellm/llms/your_provider/`
- ✅ DO: Rebase on `main` regularly to get updates
- ❌ DON'T: Modify core files unless absolutely necessary

**Why**:
- Keeps all customizations in one place
- Isolates your changes from upstream updates
- Makes conflict resolution easier

---

## Daily Development Workflow

### 1. Start Working
```bash
# Always work on custom-provider branch
git checkout custom-provider

# Make sure you have latest changes from your fork
git pull origin custom-provider
```

### 2. Create Your Provider Structure
```bash
# Create provider directory
mkdir -p litellm/llms/your_provider

# Create provider files
touch litellm/llms/your_provider/__init__.py
touch litellm/llms/your_provider/transformation.py
touch litellm/llms/your_provider/config.py
```

**Recommended file structure**:
```
litellm/llms/your_provider/
├── __init__.py           # Main provider implementation
├── transformation.py     # Input/output transformations
├── config.py            # Provider-specific configuration
└── README.md            # Provider documentation
```

### 3. Implement Your Provider
**Example structure** (`litellm/llms/your_provider/__init__.py`):
```python
from typing import Optional, Union
from litellm.llms.base import BaseLLM

class YourProviderConfig:
    """Configuration for your provider"""
    api_base: str = "https://your-api.com"
    api_key: Optional[str] = None
    # Add your config parameters

def completion(
    model: str,
    messages: list,
    api_key: Optional[str] = None,
    **kwargs
):
    """
    Your provider completion implementation
    """
    # Your implementation here
    pass

def embedding(
    model: str,
    input: Union[str, list],
    api_key: Optional[str] = None,
    **kwargs
):
    """
    Your provider embedding implementation
    """
    # Your implementation here
    pass
```

### 4. Register Your Provider
Minimize changes to core files. Only modify:

**`litellm/llms/__init__.py`**:
```python
# Add your provider import
from litellm.llms.your_provider import completion as your_provider_completion

# Register in the provider mapping
custom_provider_map = {
    "your_provider": your_provider_completion,
    # ... existing providers
}
```

### 5. Commit Your Changes
```bash
# Check what you've changed
git status

# Add your files
git add litellm/llms/your_provider/
git add litellm/llms/__init__.py  # Only if you modified it

# Commit with descriptive message
git commit -m "feat: add YourProvider implementation

- Implement completion and embedding endpoints
- Add transformation logic for input/output
- Register provider in main router"

# Push to your fork
git push origin custom-provider
```

**Commit message best practices**:
- Use conventional commits: `feat:`, `fix:`, `docs:`, `refactor:`
- First line: brief summary (50 chars or less)
- Blank line
- Detailed description if needed

### 6. Test Your Changes
```bash
# Install development dependencies
make install-dev

# Run tests
make test

# Run specific provider tests
poetry run pytest tests/llm_translation/test_your_provider.py -v

# Test your provider directly
poetry run python -c "
import litellm
response = litellm.completion(
    model='your_provider/model-name',
    messages=[{'role': 'user', 'content': 'Hello'}]
)
print(response)
"
```

---

## Weekly/Monthly Sync Routine

### Full Sync Process
```bash
# Step 1: Switch to main branch
git checkout main
# What it does: Changes your working directory to the main branch
# Why: You need to be on main to update it with upstream changes

# Step 2: Pull latest changes from official LiteLLM
git pull upstream main
# What it does:
#   - Fetches latest commits from BerriAI/litellm (upstream)
#   - Merges them into your local main branch
# Why: Gets the latest updates, bug fixes, and features

# Step 3: Push updated main to your fork
git push origin main
# What it does: Pushes your updated main branch to GitHub
# Why: Keeps your fork's main branch synchronized on GitHub

# Step 4: Switch to your custom branch
git checkout custom-provider
# What it does: Switches to your working branch
# Why: Now you're ready to apply updates to your custom code

# Step 5: Rebase your changes on updated main
git rebase main
# What it does:
#   - Temporarily removes your custom commits
#   - Fast-forwards to the updated main
#   - Re-applies your commits one-by-one on top
# Why: Keeps clean, linear history; your changes appear as if
#      they were written on the latest code

# Step 6: Resolve any conflicts (if needed)
# See "Conflict Resolution" section below

# Step 7: Force push with safety check
git push origin custom-provider --force-with-lease
# What it does: Updates GitHub with your rebased branch
# Why force push needed: Rebase rewrites history, normal push would fail
# Why --force-with-lease: Only overwrites if nobody else pushed
#                         (safer than --force)
```

### Visual Representation

**Before rebase**:
```
main:             A---B---C---D (new upstream commits)
                   \
custom-provider:    E---F---G (your custom commits)
```

**After rebase**:
```
main:             A---B---C---D
                               \
custom-provider:                E'---F'---G' (re-applied on top)
```

### Alternative: Merge Strategy (Not Recommended)
```bash
# Instead of rebase, you could merge
git checkout custom-provider
git merge main
git push origin custom-provider  # No force push needed
```

**Why rebase is better**:
- ✅ Clean, linear history
- ✅ Easy to see what YOU changed
- ✅ Easier to review and debug
- ✅ Can cherry-pick or reorder commits

**Why merge has downsides**:
- ❌ Creates merge commits cluttering history
- ❌ Harder to see your actual changes
- ❌ More complex git graph

---

## Conflict Resolution

### When Conflicts Occur
Conflicts happen when both you and upstream modified the same lines of code.

```bash
git rebase main
# Output:
# Auto-merging litellm/llms/__init__.py
# CONFLICT (content): Merge conflict in litellm/llms/__init__.py
# error: could not apply f2e3a1c... feat: add YourProvider
```

### Resolution Steps

#### 1. Identify Conflicted Files
```bash
git status
# Shows files with conflicts marked as "both modified"
```

#### 2. Open Conflicted File
You'll see conflict markers:
```python
<<<<<<< HEAD (current change - from main)
# Upstream code
from litellm.llms.openai import completion as openai_completion
=======
# Your code
from litellm.llms.your_provider import completion as your_provider_completion
>>>>>>> f2e3a1c (feat: add YourProvider)
```

#### 3. Resolve the Conflict
Edit the file to keep both changes:
```python
# Keep both imports
from litellm.llms.openai import completion as openai_completion
from litellm.llms.your_provider import completion as your_provider_completion
```

Remove conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`).

#### 4. Mark as Resolved
```bash
# Stage the resolved file
git add litellm/llms/__init__.py

# Continue the rebase
git rebase --continue
```

#### 5. If Multiple Conflicts
Rebase applies commits one-by-one, so you might need to resolve conflicts multiple times:
```bash
# After each resolution
git add <resolved-files>
git rebase --continue

# Repeat until rebase completes
```

#### 6. If It Gets Too Complex
```bash
# Abort and try a different approach
git rebase --abort

# You're back to before the rebase
# Consider:
# 1. Using merge instead: git merge main
# 2. Asking for help
# 3. Recreating custom-provider from scratch on new main
```

### Common Conflict Scenarios

#### Scenario 1: Provider Registration Conflicts
**File**: `litellm/llms/__init__.py`

**Why it happens**: Upstream added new providers in the same area

**Resolution**: Keep both upstream providers AND your provider
```python
# Upstream added:
from litellm.llms.new_provider import completion as new_provider_completion

# You added:
from litellm.llms.your_provider import completion as your_provider_completion

# Keep both!
```

#### Scenario 2: Type Definition Conflicts
**File**: `litellm/types/llms/openai.py`

**Why it happens**: Upstream modified type definitions you also use

**Resolution**: Usually prefer upstream changes unless you have specific needs
```python
# If upstream improved type safety, use their version
# Only keep your changes if they're essential for your provider
```

#### Scenario 3: Router Logic Conflicts
**File**: `litellm/router.py`

**Why it happens**: You modified routing logic

**Resolution**: Avoid modifying core files - use configuration instead
```python
# Instead of modifying router.py, use YAML config:
# config.yaml
model_list:
  - model_name: your-custom-model
    litellm_params:
      model: your_provider/model-name
```

---

## Best Practices

### 1. Minimize Core File Changes
**Good - Isolated provider**:
```
Modified files:
  litellm/llms/your_provider/__init__.py (new)
  litellm/llms/your_provider/transformation.py (new)
  litellm/llms/__init__.py (minimal change - just registration)
```

**Bad - Too many core modifications**:
```
Modified files:
  litellm/main.py
  litellm/router.py
  litellm/types/utils.py
  litellm/integrations/custom_logger.py
  ... (many core files)
```

### 2. Use Configuration Over Code
Prefer YAML configuration for customization:
```yaml
# proxy_config.yaml
model_list:
  - model_name: your-gpt-4
    litellm_params:
      model: your_provider/gpt-4-equivalent
      api_base: https://your-api.com
      api_key: os.environ/YOUR_API_KEY
      custom_llm_provider: your_provider

general_settings:
  master_key: os.environ/LITELLM_MASTER_KEY
```

### 3. Document Your Changes
Create a `CUSTOM_CHANGES.md` in your fork:
```markdown
# Custom Modifications

## Your Provider Implementation
- Location: `litellm/llms/your_provider/`
- Purpose: Integration with YourCompany's LLM API
- Modified core files:
  - `litellm/llms/__init__.py` - Added provider registration

## Testing
- Run tests: `poetry run pytest tests/llm_translation/test_your_provider.py`
- Manual test: `python examples/your_provider_test.py`

## Configuration
- See `proxy_config.yaml` for deployment settings
```

### 4. Regular Sync Schedule
```bash
# Weekly: Quick check for updates
git fetch upstream
git log main..upstream/main  # See what's new

# Monthly: Full sync and rebase
# Run the full sync routine (see above)

# Before major deployment: Always sync
```

### 5. Test After Each Sync
```bash
# After rebasing on main
git checkout custom-provider

# Run full test suite
make test

# Test your provider specifically
make test-integration
poetry run pytest tests/llm_translation/test_your_provider.py -v

# Test in proxy mode if you use it
poetry run python proxy_server.py --config proxy_config.yaml
```

### 6. Keep Provider Self-Contained
Your provider should work independently:
```python
# litellm/llms/your_provider/__init__.py

# Bad - depending on other providers
from litellm.llms.openai import openai_completion
def completion(**kwargs):
    return openai_completion(**kwargs)  # Don't do this

# Good - self-contained implementation
def completion(**kwargs):
    # Your own implementation
    response = call_your_api(**kwargs)
    return transform_response(response)
```

### 7. Version Tracking
Tag your releases to track which upstream version you're based on:
```bash
# After successful sync and testing
git tag -a v1.0.0-custom-2025-01-15 -m "Based on upstream v1.25.0"
git push origin v1.0.0-custom-2025-01-15

# List your versions
git tag -l
```

---

## Troubleshooting

### Problem: Force Push Rejected
```bash
git push origin custom-provider --force-with-lease
# error: failed to push some refs
```

**Cause**: Someone else (or you from another machine) pushed to the branch

**Solution**:
```bash
# Fetch latest
git fetch origin

# Check what's different
git log HEAD..origin/custom-provider

# Rebase on remote version
git rebase origin/custom-provider

# Then retry force push
git push origin custom-provider --force-with-lease
```

### Problem: Too Many Conflicts
```bash
git rebase main
# CONFLICT in 15 files!
```

**Solution 1 - Abort and merge instead**:
```bash
git rebase --abort
git merge main
git push origin custom-provider
```

**Solution 2 - Recreate branch**:
```bash
# Backup your changes
git diff main custom-provider > my_changes.patch

# Recreate branch from new main
git checkout main
git pull upstream main
git branch -D custom-provider
git checkout -b custom-provider

# Re-apply your changes manually or:
git apply my_changes.patch
```

### Problem: Lost Commits After Force Push
```bash
# Oh no, I force pushed and lost work!
```

**Solution - Use reflog**:
```bash
# Find your lost commits
git reflog
# Look for your commits before the force push

# Recover to that commit
git reset --hard HEAD@{5}  # Replace 5 with your reflog entry

# Create backup branch
git branch backup-recovery

# Try again more carefully
```

### Problem: Not Sure What Changed Upstream
```bash
# Before pulling, see what's new
git fetch upstream
git log --oneline main..upstream/main

# See the full diff
git diff main upstream/main

# See which files changed
git diff --name-only main upstream/main
```

### Problem: Accidentally Committed to Main
```bash
# Oh no! I committed custom changes to main
git checkout main
# (made changes and committed)
```

**Solution**:
```bash
# Move the commits to custom-provider
git checkout custom-provider
git merge main  # Get the commits

# Reset main to match upstream
git checkout main
git reset --hard upstream/main
git push origin main --force-with-lease

# Now main is clean and custom-provider has your changes
```

---

## Quick Reference

### Common Commands
```bash
# Daily work
git checkout custom-provider
git add <files>
git commit -m "message"
git push origin custom-provider

# Weekly sync
git checkout main && git pull upstream main && git push origin main
git checkout custom-provider && git rebase main
git push origin custom-provider --force-with-lease

# Check status
git status                    # Current changes
git log --oneline -10        # Recent commits
git remote -v                # Remote repositories
git branch -a                # All branches

# Conflict resolution
git rebase main              # Start rebase
# (fix conflicts)
git add <files>              # Stage resolved files
git rebase --continue        # Continue rebase
git rebase --abort          # Abort if needed

# Emergency recovery
git reflog                   # See all recent actions
git reset --hard HEAD@{n}   # Go back to previous state
```

### File Structure
```
your-fork/
├── litellm/
│   ├── llms/
│   │   ├── your_provider/        # Your custom provider
│   │   │   ├── __init__.py
│   │   │   ├── transformation.py
│   │   │   └── config.py
│   │   └── __init__.py           # Modified: provider registration
│   └── ...
├── tests/
│   └── llm_translation/
│       └── test_your_provider.py # Your provider tests
├── DEV_FLOW.md                   # This file
└── CUSTOM_CHANGES.md             # Document your modifications
```

---

## Additional Resources

- **LiteLLM Docs**: https://docs.litellm.ai/
- **Contributing Guide**: https://github.com/BerriAI/litellm/blob/main/CONTRIBUTING.md
- **Git Rebase Tutorial**: https://git-scm.com/docs/git-rebase
- **Provider Examples**: Check `litellm/llms/` for reference implementations

---

**Last Updated**: 2025-11-11
**Maintainer**: Your Name / Team
**Based on**: LiteLLM upstream (https://github.com/BerriAI/litellm)
