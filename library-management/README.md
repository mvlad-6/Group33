# Library Management System (LMS)

A small Flask REST API for tracking books, members, and loans. Data is stored
**in memory** (plain Python objects, no database) and is reset every time the
app restarts — this project is meant to run before you've covered databases.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

The API runs at `http://127.0.0.1:5000`.

## Web UI

Open `http://127.0.0.1:5000/` in a browser for a basic HTML front end (plain
forms and tables, no JavaScript) to add/delete books and members, and check
books in/out:

| Page | Path |
|---|---|
| Home | `/` |
| Books | `/ui/books` |
| Members | `/ui/members` |
| Loans | `/ui/loans` |

This UI is separate from the JSON API below — it's there so you can see the
app working without a REST client, and calls the same in-memory store.

## Entities

- **Book**: `id, title, author, isbn, total_copies, available_copies`
- **Member**: `id, name, email, membership_date`
- **Loan**: `id, book_id, member_id, loan_date, due_date, return_date`

## JSON API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/books` | List all books |
| POST | `/books` | Create a book |
| GET | `/books/<id>` | Get one book |
| PUT | `/books/<id>` | Update a book |
| DELETE | `/books/<id>` | Delete a book |
| GET | `/members` | List all members |
| POST | `/members` | Create a member |
| GET | `/members/<id>` | Get one member |
| PUT | `/members/<id>` | Update a member |
| DELETE | `/members/<id>` | Delete a member |
| POST | `/loans` | Check out a book (`book_id`, `member_id`); respects the first waiting reservation and requires an available copy |
| PUT | `/loans/<id>/return` | Return a loaned book |
| GET | `/loans?member_id=&book_id=` | Look up loans |
| GET | `/reservations?member_id=&book_id=` | List reservations, optionally filtered by member or book |
| POST | `/reservations` | Reserve a book (`book_id`, `member_id`) |

## Reservation checkout enhancement (Joshua, R19)

Create a reservation with `POST /reservations`, for example
`{"book_id": 1, "member_id": 2}`. After a copy is returned, use
`POST /loans` with the same book and member IDs to borrow it.

API checkout checks unfulfilled reservations in creation order. Only the
member with the first waiting reservation can borrow that book while a
reservation is pending. Successful checkout marks that reservation fulfilled
and decreases availability. This is a simple first-in-first-out policy,
including when a title has multiple copies; reservation expiry is not implemented.

Checkout returns 409 with `No copies available` if availability is zero or
negative, or `Book reserved for another member` if another member is first
in line. Rejected requests do not create a loan or fulfill a reservation.
With no waiting reservation, normal API checkout is unchanged except for
the availability check.

This enhancement applies to the JSON API. The existing HTML checkout form
uses separate code and does not enforce these rules. Member authentication
is also absent, so R19 is only partially satisfied by this enhancement.

## Tests

```bash
pytest
```
