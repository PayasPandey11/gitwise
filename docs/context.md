---
layout: default
title: "Context Management - GitWise"
---

# Context Management in GitWise

## Overview

GitWise's Context Management feature enhances the quality of AI-generated outputs by providing the AI with crucial information about the "why" behind your code changes. This context helps the AI produce more relevant commit messages, PR descriptions, and other AI-assisted content.

## Why Context Matters

Without context, AI can only analyze the "what" (the code changes) but lacks understanding of:
- The purpose behind changes
- Ticket/issue requirements
- Project-specific terminology
- Development goals and intent

By providing context, you get:
- More accurate commit messages
- More relevant PR descriptions
- Better alignment with actual development work
- Improved understanding of technical terminology

## Basic Usage

### Setting Context

```bash
gitwise set-context "Working on user authentication with JWT tokens"
```

This stores context information for your current branch. The context is used when generating commit messages and PR descriptions.

### Viewing Current Context

```bash
gitwise get-context
```

Shows:
- User-provided context
- Ticket IDs parsed from branch names
- Keywords extracted from branch names
- Last update timestamp

## How It Works

### Context Storage

GitWise stores context per branch in JSON files located at:
```
.git/gitwise/context/<branch_name>.json
```

The context files contain:
```json
{
  "user_set_context": "User's explicitly set goal or description",
  "parsed_ticket_id": "TICKET-123",
  "parsed_keywords": ["authentication", "login"],
  "last_updated": 1623456789
}
```

### Automatic Context Parsing

Even without manual context, GitWise tries to extract context from:
1. **Branch Names**: Parses ticket IDs like `feature/JIRA-123-login-page`
2. **Keywords**: Extracts significant terms from branch names

### Context in Commit Messages

When running `gitwise commit`, the system:
1. Checks for stored context for the current branch
2. If no context exists, tries to parse from branch name
3. If still no context, optionally prompts the user
4. Includes the context in the AI prompt for generating the commit message
5. Shows which context is being used with a visual indicator

### Context in PR Descriptions

Similarly, when running `gitwise pr`, the context is used to enrich the PR description, ensuring it aligns with the development purpose.

## Advanced Usage

### Context for Multiple Branches

Each branch maintains its own context, allowing you to work on multiple features simultaneously while keeping context separate:

```bash
# Working on feature branch
gitwise checkout feature/login
gitwise set-context "Implementing secure login with 2FA"

# Switch to another branch
gitwise checkout feature/dashboard
gitwise set-context "Creating analytics dashboard with charts"
```

### Updating Context

Simply run `set-context` again to update:

```bash
gitwise set-context "Updated focus: Adding OAuth support to login"
```

### Context for Tickets

A powerful pattern is to include ticket details:

```bash
gitwise set-context "JIRA-123: Add login feature with requirements: username/password auth, password reset, remember me option"
```

## Best Practices

1. **Be Specific**: Include key technical details relevant to the implementation
2. **Include Ticket IDs**: Reference issue trackers when applicable
3. **Update as Focus Changes**: Keep context current as development progresses
4. **Use Branch Naming Conventions**: Follow patterns like `feature/TICKET-123-description` for automatic parsing

## Troubleshooting

### Context Not Showing in AI Output

- Verify context is set with `gitwise get-context`
- Make sure you've reinstalled GitWise after updates (`pip install -e .`)
- Check if you're on the correct branch

### Context File Issues

Context files are stored in `.git/gitwise/context/`. If you experience issues:

```bash
# View context files
ls -la .git/gitwise/context/

# Remove problematic context
rm .git/gitwise/context/<problematic_file>.json
```

---

<div class="tip-box">
  <h3>💡 Pro Tip</h3>
  <p>Set context at the beginning of your feature work to ensure all commits and PRs benefit from the additional information. This is especially valuable for complex features spanning multiple days of work.</p>
</div> 