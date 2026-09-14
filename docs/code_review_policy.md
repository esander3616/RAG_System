# Code Review Process

## Purpose

Code review exists to catch defects before they reach production, maintain a consistent standard of quality across the codebase, and spread knowledge of the system across the team. Every change to a shared repository goes through this process before merging.

## Submission

Developers open a pull request against the main branch once their change is ready for review. The pull request description should explain what changed and why, and should link to any related ticket. Pull requests should be kept reasonably small and focused on a single change where practical, since smaller changes are reviewed faster and more thoroughly.

## Turnaround Time

Reviewers are expected to provide initial feedback on a pull request within 48 hours (2 business days) of submission. This is the standard turnaround commitment across all engineering teams. If a reviewer cannot meet this window due to competing priorities, they should flag this to the pull request author immediately so an alternate reviewer can be assigned. Pull requests that remain without any reviewer response after 48 hours should be escalated to the team lead.

## Review Criteria

A reviewer evaluates a pull request on five dimensions: functionality (does the code do what it claims to do), complexity (could this be simpler), test coverage (are the changes adequately tested), readability (would another engineer understand this code six months from now), and naming (are variables, functions, and classes named clearly). A reviewer should leave specific, actionable comments rather than vague objections.

## Approval and Merge

At least one approval is required before a pull request can be merged into the main branch. For changes touching authentication, billing, or customer data, two approvals are required, with at least one from a senior engineer on the owning team. The author is responsible for addressing all reviewer comments or explaining why a suggested change was not made before merging.

## Escalation

If a reviewer and author cannot reach agreement after two rounds of comments, either party may request a third opinion from the team lead. The team lead's decision on the disputed point is final for the purposes of that pull request.