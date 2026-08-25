# profScope
# ProfScope

**Professional OSINT Profile Discovery Tool**

ProfScope is a lightweight Python/FastAPI-based OSINT tool designed to help users quickly discover publicly available professional profiles associated with a person.

The initial version generates targeted searches across professional platforms such as LinkedIn, GitHub, GitLab, Stack Overflow, and Medium.

> **Important:** ProfScope is intended for legitimate OSINT, research, recruitment, professional networking, and cybersecurity use. It should only work with publicly available information and should respect the terms, APIs, rate limits, and policies of each platform.

---

## 1. Problem Statement

When conducting legitimate OSINT or professional research, a user may need to search several platforms individually.

For example:

```text
Google
   ↓
Search person's name
   ↓
LinkedIn
   ↓
Search again
   ↓
GitHub
   ↓
Search again
   ↓
GitLab
   ↓
Search again
   ↓
Stack Overflow