# Backlog

Repository of future work items, improvements, and bug fixes not yet in active development.

## Structure

```
docs/backlog/
├── README.md                    # This file
├── bugs/                        # Known issues and bug reports
│   └── README.md               # Bug tracking guide
├── features/                    # Feature requests and enhancements
│   └── README.md               # Feature proposal guide
└── refactors/                   # Technical debt and refactoring tasks
    └── README.md               # Refactoring guide
```

## Workflow

### Moving Items from Backlog to Development

When a backlog item is selected for implementation:

1. **Move from backlog to development**
   ```bash
   # Copy bug from backlog to development
   cp docs/backlog/bugs/ITEM.md docs/development/fixes/ITEM.md
   
   # Copy feature from backlog to development
   cp docs/backlog/features/ITEM.md docs/development/features/ITEM.md
   
   # Copy refactor from backlog to development
   cp docs/backlog/refactors/ITEM.md docs/development/refactors/ITEM.md
   ```

2. **Create implementation branch**
   ```bash
   git checkout -b feature/ITEM-name
   # or
   git checkout -b fix/ITEM-name
   ```

3. **Implement the feature/fix**
   - Follow development guidelines
   - Update development folder documentation
   - Create commits as needed

4. **Complete and move to commits**
   ```bash
   # After implementation complete
   cp docs/development/features/ITEM.md docs/commits/features/ITEM.md
   # or
   cp docs/development/fixes/ITEM.md docs/commits/fixes/ITEM.md
   ```

## Item States

### Backlog (📋)
- Not yet selected for implementation
- Under review or consideration
- May need more specification

### Development (🚀)
- Actively being worked on
- In progress implementation
- Branch created and active

### Commits (✅)
- Implementation complete
- Merged to main branch
- Historical record of completed work

## Guidelines

### Creating Backlog Items

Use clear, descriptive filenames:
- `bug-DESCRIPTION.md` - Bug reports
- `feature-DESCRIPTION.md` - Feature requests
- `refactor-DESCRIPTION.md` - Refactoring tasks

Include sections:
- **Title** - Clear, concise name
- **Description** - What needs to be done
- **Motivation** - Why it's important
- **Acceptance Criteria** - Definition of done
- **Effort Estimate** - Small/Medium/Large
- **Related Items** - Links to other issues/features
- **Notes** - Additional information

### Prioritization

Backlog items are prioritized by:
1. **Criticality** - Impact on system reliability
2. **Value** - Business or user value
3. **Effort** - Implementation complexity
4. **Dependencies** - Blocked by other items

## Querying Backlog

### View all bugs
```bash
ls -1 docs/backlog/bugs/*.md
```

### View all features
```bash
ls -1 docs/backlog/features/*.md
```

### View all refactors
```bash
ls -1 docs/backlog/refactors/*.md
```

### Search backlog
```bash
grep -r "keyword" docs/backlog/
```

## Statistics

Track backlog metrics:
- Total items in backlog
- Items by priority
- Items by effort estimate
- Items blocked by dependencies

## See Also

- **[Development](../development/)** - Items in active development
- **[Commits](../commits/)** - Completed work
- **[Implementation Plan](../plan.md)** - Overall roadmap
- **[Project Status](../project-structure-status.md)** - Current progress
