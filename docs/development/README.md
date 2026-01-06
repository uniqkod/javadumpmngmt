# Development

Active work in progress. Items being implemented for current sprint or development cycle.

## Structure

```
docs/development/
├── README.md                    # This file
├── features/                    # Features in active development
│   └── README.md               # Feature development guide
├── fixes/                       # Bug fixes in active development
│   └── README.md               # Bug fix development guide
└── refactors/                   # Refactorings in active development
    └── README.md               # Refactoring development guide
```

## Workflow

### Moving Items from Backlog to Development

When a backlog item is selected for implementation:

```bash
# 1. Copy item from backlog to development
cp docs/backlog/features/feature-name.md docs/development/features/feature-name.md
# or
cp docs/backlog/bugs/bug-name.md docs/development/fixes/bug-name.md
# or
cp docs/backlog/refactors/refactor-name.md docs/development/refactors/refactor-name.md

# 2. Create implementation branch
git checkout -b feature/feature-name
# or
git checkout -b fix/bug-name
# or
git checkout -b refactor/area-name

# 3. Update the development document with progress
# - Add implementation details
# - Document decisions made
# - Link to commits/PRs
# - Update status

# 4. Implement the work
# - Write code
# - Create commits
# - Push to branch
# - Create pull request

# 5. Move to commits when complete
cp docs/development/features/feature-name.md docs/commits/features/feature-name.md
```

## Item States

### In Development (🚀)
- Actively being worked on
- Implementation in progress
- Branch created and active
- WIP (Work in Progress)

### In Review (👀)
- Pull request created
- Code review underway
- May have requested changes

### Ready to Merge (✅)
- Approved by reviewers
- All checks passing
- Ready for merge to main branch

### Complete (📦)
- Merged to main branch
- Move to `docs/commits/`
- Archive development document

## Documentation During Development

### Update Status Section

```markdown
## Status

**Current State:** In Development
**Branch:** feature/feature-name
**PR:** #123 (link to GitHub PR)
**Progress:** 60% complete

### Timeline
- Started: 2026-01-05
- Current: 2026-01-06
- Expected Completion: 2026-01-10
```

### Track Implementation Details

```markdown
## Implementation Progress

### Completed
- [ ] Item 1
- [ ] Item 2

### In Progress
- [ ] Item 3
- [ ] Item 4

### Remaining
- [ ] Item 5
- [ ] Item 6
```

### Document Decisions Made

```markdown
## Technical Decisions

### Decision 1
**Context:** Why this decision was needed
**Options Considered:** 
- Option A - pros/cons
- Option B - pros/cons
**Decision:** Chose Option A
**Rationale:** Why we chose this option
**Trade-offs:** What we sacrifice

### Decision 2
...
```

### Link to Work

```markdown
## Git Information

**Branch:** feature/mount-access-controller
**Commit Range:** abc123..def456

Related commits:
- abc123 - feat: core implementation
- def456 - test: add unit tests
- ghi789 - docs: update documentation

PR: https://github.com/org/repo/pull/123
```

## Querying Development Items

### View all features in development
```bash
ls -1 docs/development/features/*.md
```

### View all fixes in development
```bash
ls -1 docs/development/fixes/*.md
```

### View all refactors in development
```bash
ls -1 docs/development/refactors/*.md
```

### Search development items
```bash
grep -r "keyword" docs/development/
```

### Check status of all items
```bash
grep -h "## Status" docs/development/*/*.md
```

## Management

### Prioritize Items

Development items are prioritized by:
1. **Criticality** - Impact on system reliability
2. **Dependencies** - Blocked/blocking other work
3. **Timeline** - Sprint/release deadlines
4. **Effort** - Implementation complexity

### Track Progress

Keep documents updated with:
- Current status
- Percentage complete
- Blockers or issues
- Changes in timeline
- Key decisions made
- Test results
- Performance metrics

### Handle Blockers

If blocked:
1. Document the blocker clearly
2. Identify root cause
3. Flag for team discussion
4. Link to related issue
5. Update status regularly

### Communicate Changes

If scope/timeline changes:
1. Update development document
2. Add note explaining change
3. Discuss with team
4. Update related backlog item
5. Adjust timeline if needed

## Best Practices

### Keep Documentation Updated

- Update status daily or weekly
- Document decisions as made
- Link commits as they're created
- Note any changes in scope
- Record blockers immediately
- Include test results
- Document lessons learned

### Clear Commit Messages

```
feat: add mount-access-controller

- Implement controller class
- Add mount monitoring
- Implement recovery logic
- Add K8s integration
- Include unit tests

Related: docs/development/features/mount-access-controller.md
```

### Link Pull Requests

```
## Pull Request

Created: https://github.com/org/repo/pull/123
Status: In Review
Last Updated: 2026-01-06

Changes:
- [ ] Code written
- [ ] Tests added
- [ ] Docs updated
- [ ] Code reviewed
- [ ] Approved
- [ ] Merged
```

### Testing During Development

```
## Testing

### Unit Tests
- [ ] Test component X
- [ ] Test component Y
- Coverage: 85%

### Integration Tests
- [ ] Test with component Z
- [ ] Test end-to-end flow

### Performance Tests
- Baseline: X ms
- Current: Y ms
- Status: ✅ Within acceptable range
```

## Completion Checklist

Before moving item to commits:

- [ ] Feature/fix implemented
- [ ] All tests passing
- [ ] Code reviewed and approved
- [ ] Documentation updated
- [ ] CHANGELOG updated
- [ ] No breaking changes (or documented)
- [ ] Performance metrics acceptable
- [ ] Pull request merged
- [ ] Development document complete
- [ ] Ready to move to commits folder

## Integration with Other Folders

### From Backlog
- Copy item from `docs/backlog/[type]/`
- Update with progress as you work
- Keep linked to backlog item

### To Commits
- Move to `docs/commits/[type]/`
- Finalize documentation
- Include final metrics
- Create historical record

## See Also

- **[Backlog](../backlog/)** - Future work items
- **[Commits](../commits/)** - Completed work
- **[Root README](../../README.md)** - Project overview
- **[Implementation Plan](../plan.md)** - Overall roadmap
- **[Project Status](../project-structure-status.md)** - Current progress
