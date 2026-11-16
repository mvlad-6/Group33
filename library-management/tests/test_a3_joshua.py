from datetime import date, timedelta
from unittest.mock import patch

from app import store
from app.models.loan import Loan


def test_overdue_reminder_reports_notification_failure(client, monkeypatch):
    member = client.post("/members", json={"name": "Reader", "email": "reader@example.com"}).get_json()
    loan = Loan(id=1, book_id=1, member_id=member["id"], due_date=date.today() - timedelta(days=3))
    store.loans[loan.id] = loan
    monkeypatch.setattr("app.routes.loans.send_notification", lambda recipient, subject, message: False)

    response = client.get("/loans/overdue")

    assert response.status_code == 200
    assert response.get_json() == [{**loan.to_dict(), "notified": False}]
    assert store.loans[loan.id].return_date is None


def test_overdue_reminder_skips_returned_and_future_loans(client):
    today = date.today()
    store.loans[1] = Loan(1, 1, 1, today - timedelta(days=3), return_date=today)
    store.loans[2] = Loan(2, 1, 1, today + timedelta(days=3))

    with patch("app.routes.loans.send_notification") as send:
        response = client.get("/loans/overdue")

    assert response.status_code == 200
    assert response.get_json() == []
    send.assert_not_called()


def test_book_form_adds_and_deletes_book(client):
    response = client.post(
        "/ui/books",
        data={"title": "Library Book", "author": "Author", "isbn": "12345", "total_copies": "2"},
        follow_redirects=True,
    )

    assert b"Library Book" in response.data
    book = next(iter(store.books.values()))
    assert book.available_copies == book.total_copies == 2

    response = client.post(f"/ui/books/{book.id}/delete", follow_redirects=True)

    assert b"Library Book" not in response.data
    assert book.id not in store.books


def test_member_form_adds_and_deletes_member(client):
    response = client.post(
        "/ui/members",
        data={"name": "Library Reader", "email": "reader@example.com"},
        follow_redirects=True,
    )

    assert b"Library Reader" in response.data
    member = next(iter(store.members.values()))
    assert member.email == "reader@example.com"

    response = client.post(f"/ui/members/{member.id}/delete", follow_redirects=True)

    assert b"Library Reader" not in response.data
    assert member.id not in store.members


def test_loan_form_checkout_and_repeat_return(client):
    client.post("/ui/books", data={"title": "Book", "author": "Author", "isbn": "12345", "total_copies": "1"})
    client.post("/ui/members", data={"name": "Reader", "email": "reader@example.com"})
    book = next(iter(store.books.values()))
    member = next(iter(store.members.values()))

    response = client.post(
        "/ui/loans", data={"book_id": book.id, "member_id": member.id}, follow_redirects=True
    )

    assert response.request.path == "/ui/loans"
    loan = next(iter(store.loans.values()))
    assert (loan.book_id, loan.member_id) == (book.id, member.id)
    assert loan.return_date is None
    assert book.available_copies == 0

    response = client.post(f"/ui/loans/{loan.id}/return", follow_redirects=True)
    assert response.request.path == "/ui/loans"
    assert loan.return_date == date.today()
    assert book.available_copies == 1

    client.post(f"/ui/loans/{loan.id}/return")
    assert book.available_copies == 1


def test_loan_form_skips_missing_book(client):
    response = client.post("/ui/loans", data={"book_id": "999", "member_id": "1"})

    assert response.location == "/ui/loans"
    assert not store.loans


def test_home_page_links_to_library_views(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b"<h1>Library Management System</h1>" in response.data
    assert b'href="/ui/books">Books</a>' in response.data
    assert b'href="/ui/members">Members</a>' in response.data
    assert b'href="/ui/loans">Loans</a>' in response.data
