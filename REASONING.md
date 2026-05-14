# Design Reasoning

This document records the design choices I made while building the library lending API, why I made them, and what I would change with more time. New sections get added as decisions are made in code.

## Why SQLite over Postgres
SQLite is build in Python.Nothing to install,nothing to run as a seperate program.

I figured it out that SQLite handles everything we need for this project's size including:foreign keys,joins,the M:N table,the reports.


## How I modelled the M:N books ↔ authors relationship

A many-to-many relationship can't be done with a single foreign key on either side. The table books_authors handles that relationship. It has only two columns "book_id" and "author_id",both columns together form the primary key, this prevents the same pair for being listed twice.

I declared book_authors as a SQLAlchemy Table, not a class since it doesn't have extra columns-it's just a link.

Compare with loans:the loans table is also in between two tables, but it has other columns other than the keys,which makes it a real entity,not just a link, so it gets a class.

## Why I used Alembic for schema management

Without Alembic, this project has no working database. The python models in models.py describe the schema in code but they don't create anything. alembic upgrade head does that.

## Why DELETE on a member or book with active loans returns 409

Deleting a member with active loans would either silently destroy the loan record (if we used CASCADE) or fail with a database-level error (the FK constraint without CASCADE). Neither is acceptable UX.