# Backend Development Guidelines

> Best practices for backend development in this project.

---

## Overview

This directory contains the current backend conventions for codercheckin, a
Python 3.11 multi-platform check-in automation service. The project is packaged
as a single repo with root-level orchestration modules plus small packages for
platform integrations and external services.

---

## Guidelines Index

| Guide | Description | Status |
|-------|-------------|--------|
| [Directory Structure](./directory-structure.md) | Module organization and file layout | Filled |
| [Database Guidelines](./database-guidelines.md) | ORM patterns, queries, migrations | Filled |
| [Error Handling](./error-handling.md) | Error types, handling strategies | Filled |
| [Quality Guidelines](./quality-guidelines.md) | Code standards, forbidden patterns | Filled |
| [Logging Guidelines](./logging-guidelines.md) | Structured logging, log levels | Filled |

---

## Pre-Development Checklist

Before editing backend code:

1. Read [Directory Structure](./directory-structure.md) before adding or moving
   modules.
2. Read [Error Handling](./error-handling.md) before changing process flow,
   network calls, or target execution.
3. Read [Logging Guidelines](./logging-guidelines.md) before adding log output.
4. Read [Quality Guidelines](./quality-guidelines.md) before writing or updating
   tests.
5. Read [Database Guidelines](./database-guidelines.md) only if a change proposes
   persistent storage; the current project intentionally has no database layer.

---

**Language**: All documentation should be written in **English**.
