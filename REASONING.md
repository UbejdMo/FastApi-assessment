# Design Reasoning

This document records the design choices I made while building the library lending API, why I made them, and what I would change with more time. New sections get added as decisions are made in code.

## Why SQLite over Postgres

I chose SQLite over Postgres for this assessment. It ships in Python's standard library, requires no separate service to install or run, and supports every feature this assessment needs — including foreign keys, composite primary keys for the M:N association table, and the joins and aggregations the search and reports endpoints require. SQLAlchemy abstracts the engine away, so if the project grew to need concurrent writes or a real production deployment, swapping to Postgres would be a connection-string change plus a migration tool, not a rewrite.

## External resources used

- (Running list. Every documentation page, tutorial, and AI prompt used during this assessment is recorded here as it happens.)