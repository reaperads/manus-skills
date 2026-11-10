---
name: skill-anti-duplicate
description: "Detect duplicate and overlapping skills using description matching, keyword analysis, and section comparison. Provides merge decision framework: which copy to keep, which to archive, and how to preserve unique content."
tags: [skills, duplicates, overlap, merge, detection]
version: 1.0.0
author: Feb
category: hermes
metadata:
  hermes:
    tags: [skills, duplicates, overlap, merge, detection]
    platforms: [linux]
---

## Working principles

- Report only bugs that are actually proven, with evidence and reproduction steps. Negative tests stay in internal notes and are never submitted. Distinguish potential vs proven vs reportable.
- Validate each hypothesis with an explicit verdict: CONFIRMED, FALSIFIED, or INCONCLUSIVE. Do not conclude "0 confirmed" prematurely — re-evaluate for missed gaps (business logic, state transitions, value limits, feature interactions) and check state changes and side effects (HTTP 200 is not success; an error is not safety).
- Test only with the user's own accounts on free tiers. Never spend capital or pay for testing. No DoS, spam, high-volume automated scanning, social engineering, or other people's data. No bypassing gates by evasion.
- Never submit anything (a report, a grade, a mainnet/testnet submission) without the user's explicit confirmation for that specific submit. Never send a report twice. Never reply to a vendor without approval.
- Follow the program's "How to report" structure (Description, Potential Impact, Evidence, Steps to Reproduce). Vendor emails open with a greeting + short intro, tidy formatting, never raw markdown as the email body.
- Communicate terse, exact, and path-first. Indonesian for conversation, English for technical detail, code, identifiers, and error strings.

# Skill Anti-Duplicate

Detect and resolve duplicate/overlapping skills. Prevents skill sprawl and ensures each domain has exactly one canonical skill.

## When to use

- After a skill audit reveals potential duplicates
- Before creating a new skill (check for existing coverage)
- User says "ada duplikat" / "skill ini sama kayak yang itu"
- Periodic dedup check (monthly)

## Detection methods

### Method 1: Exact description match

```bash
cd ~/.hermes/skills
find . -name "SKILL.md" -exec sh -c '
  desc=$(head -5 "$1" | grep "^description:" | head -1)
  echo "$desc|$1"
' _ {} \; | sort | awk -F'|' '
  {descs[$1] = descs[$1] " " $2; counts[$1]++}
  END {for (d in counts) if (counts[d] > 1) print "DUP ("counts[d]"x): " d "\n  →" descs[d] "\n"}
'
```

### Method 2: Keyword overlap matrix

```bash
cd ~/.hermes/skills
for kw in 9router qoder tokenharbor farm gateway provider proxy tempmail \
           captcha turnstile oauth inject sqlite batch signup account; do
  hits=$(grep -rl "$kw" --include="SKILL.md" . 2>/dev/null | wc -l)
  if [ "$hits" -gt 3 ]; then
    echo "=== '$kw' in $hits skills ==="
    grep -rl "$kw" --include="SKILL.md" . 2>/dev/null
    echo
  fi
done
```

Keywords appearing in 5+ skills are red flags for potential overlap.

### Method 3: Section title comparison

```bash
cd ~/.hermes/skills
# Compare section headings across skills that share keywords
for pair in "tokenharbor-farm automation/tokenharbor-account-farming" \
            "9router/9router-ops devops/9router-administration"; do
  echo "=== COMPARING: $pair ==="
  s1=$(echo $pair | cut -d' ' -f1)
  s2=$(echo $pair | cut -d' ' -f2)
  echo "--- $s1 sections ---"
  grep '^## ' "$s1/SKILL.md"
  echo "--- $s2 sections ---"
  grep '^## ' "$s2/SKILL.md"
  echo
done
```

### Method 4: Tag intersection

```bash
cd ~/.hermes/skills
# Extract tags from frontmatter and find skills with identical tag sets
find . -name "SKILL.md" -exec sh -c '
  tags=$(sed -n "/^tags:/,/^[^ -]/p" "$1" | grep "^\s*-" | tr -d " -" | sort | tr "\n" ",")
  echo "$tags|$1"
' _ {} \; | sort | awk -F'|' '
  {tags[$1] = tags[$1] " " $2; counts[$1]++}
  END {for (t in counts) if (counts[t] > 1) print "SAME TAGS: " t "\n  →" tags[t] "\n"}
'
```

## Merge decision framework

When two skills overlap, decide which to keep (canonical) and which to archive:

### Keep the one that is:
1. **More detailed** — larger, more pitfalls, more steps
2. **More recently updated** — check version/date in frontmatter
3. **Has more linked files** — references, scripts, templates
4. **Better categorized** — in a proper category dir, not root-level
5. **Referenced by other skills** — appears in "Related skills" sections

### Archive the one that is:
1. **Thinner** — fewer sections, fewer pitfalls
2. **Older** — not updated recently
3. **Root-level** — uncategorized
4. **Subset** — covers a subset of what the canonical covers

### Special case: complementary (keep both)

Two skills cover the same domain but at different abstraction levels:
- `ai-gateway-key-farming` (deep recon methodology, pateway-specific) vs `mass-account-api-key-farm` (generic playbook) → **keep both**, add cross-links
- `qoder-farm` (farming, 85KB) vs `qoder-token-management` (PAT validation, small) → **keep both**, different scopes

## Merge procedure

```
1. READ both SKILL.md files (skill_view)
2. DIFF section titles → identify unique sections in each
3. CHECK linked files → identify unique refs/scripts/templates
4. COPY unique linked files from archive-candidate → canonical skill
5. PATCH canonical SKILL.md → add any unique sections from archive-candidate
6. ADD cross-reference in canonical → "Archived: <name> (merged <date>)"
7. MV archive-candidate → .archive/
8. VERIFY canonical loads: skill_view(name=<canonical>)
```

### Example merge command sequence

```bash
# 1. Copy unique linked files
cp ~/.hermes/skills/<duplicate>/references/unique-ref.md \
   ~/.hermes/skills/<canonical>/references/
cp ~/.hermes/skills/<duplicate>/scripts/unique-script.py \
   ~/.hermes/skills/<canonical>/scripts/

# 2. Archive the duplicate
mv ~/.hermes/skills/<duplicate> ~/.hermes/skills/.archive/<duplicate>

# 3. Verify
skill_view(name=<canonical>)
```

## Known duplicate clusters (as of Aug 2026)

These clusters have been identified and resolved:

| Cluster | Canonical (kept) | Archived |
|---------|-------------------|----------|
| TokenHarbor farming | `automation/tokenharbor-account-farming` | `tokenharbor-farm` → `.archive/` |
| Generic mass farming | `automation/mass-account-api-key-farm` | `automation/mass-account-api-farming` → `.archive/` |
| 9router operations | `9router/9router-ops` (umbrella) | `9router-gateway-mgmt` → `.archive/`, `devops/9router-provider-ops` → `.archive/` |
| 9router admin (deep) | `devops/9router-administration` (kept — 95KB, unique refs) | (none archived — complementary to 9router-ops) |

## Pitfalls

1. **Never auto-merge without reading both skills.** Keyword overlap doesn't mean content overlap — two skills mentioning "9router" might cover completely different aspects (DB ops vs provider inject vs security hardening).
2. **Check linked files BEFORE archiving.** The duplicate may have unique references that the canonical doesn't. Always copy first, archive second.
3. **Some "duplicates" are intentionally split by abstraction level.** A deep-dive skill and a generic playbook serve different needs. Add cross-links, don't merge.
4. **`devops/9router-administration` (95KB, 33 refs) was kept alongside `9router/9router-ops` (67KB, 19 refs).** They're complementary — 9router-administration has deeper historical bug docs, 9router-ops has operational procedures. Merging would create a 160KB monster. Both stay.
5. **Archived skills can still be searched.** Use `grep -r` or `search_files` in `.archive/` to find old patterns. Don't hesitate to archive — retrieval is always possible.
6. **Run detection BEFORE creating new skills.** A 30-second keyword check saves a 10-minute merge later.

## Related skills

- `skill-audit` — full audit procedure including duplicate detection
- `skill-management` — lifecycle management (archive, restore, pin)
- `skill-auto-organize` — auto-categorize and trim oversized skills
- `skill-strengthen` — improve existing skills
- `skill-auto-create` — auto-generate from session patterns