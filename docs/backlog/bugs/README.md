# Bugs

Known issues and bug reports awaiting resolution.

## Organization

Bugs are organized by:
- **Status** - New, Confirmed, Under Investigation, Blocked
- **Severity** - Critical, High, Medium, Low
- **Component** - Which part of the system is affected

## Creating a Bug Report

Use this template for bug reports:

```markdown
# Bug: [Short Description]

**Status:** New  
**Severity:** Medium  
**Component:** [Component Name]  
**Reported:** [Date]

## Description

What is the issue?

## Steps to Reproduce

1. Step 1
2. Step 2
3. ...

## Expected Behavior

What should happen?

## Actual Behavior

What actually happens?

## Environment

- Kubernetes Version: 1.20+
- Component: memory-leak-app v1.0
- Reproducibility: Always/Sometimes/Rare

## Logs/Error Messages

```
error logs here
```

## Related Items

- Links to other bugs/features
- Related PRs or commits

## Notes

Additional information...
```

## Severity Levels

- **Critical** 🔴 - System broken, no workaround
- **High** 🟠 - Major functionality impaired
- **Medium** 🟡 - Feature partially working, workaround exists
- **Low** 🟢 - Minor issue, cosmetic, or edge case

## Workflow

1. **New** - Bug reported
2. **Confirmed** - Reproduced and verified
3. **Under Investigation** - Root cause being determined
4. **Blocked** - Waiting on other work/dependencies
5. **Fix in Progress** → Move to `docs/development/fixes/`
6. **Fixed** → Move to `docs/commits/fixes/`

## Current Bugs

Currently no bugs in backlog.

## Next Steps

When ready to fix a bug:
1. Copy to `docs/development/fixes/`
2. Create fix branch: `git checkout -b fix/bug-name`
3. Implement fix
4. Test thoroughly
5. Commit and push
6. Create pull request

## Guidelines

- Search existing bugs before reporting
- Include complete reproduction steps
- Provide logs and error messages
- Link related issues
- Update status as work progresses
