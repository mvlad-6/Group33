import pytest 

def test_add_book(client):
    """Tests adding book to catalog"""
    payload = {
        "title": "BookTitle",
        "author": "Tom Brady",
        "isbn": "123",
        "total_copies": 2
    }

    response = client.post("/books", json=payload)
    assert response.status_code == 201
    data = response.get_json()
    assert data["id"] == 1
    assert data["title"] == "BookTitle"
    assert data["total_copies"] == 2
    assert data["available_copies"] == 2

def test_list_books(client):
    """Tests function it list books in system"""
    client.post(
        "/books",
        json = {"title": "testbook", "author": "sally", "isbn": '5454', "total_copies": 2}
    )
    client.post(
                "/books",
                json = {"title": "book2", "author": " terry", "isbn": '2222', "total_copies": 1}
            )

    response = client.get("/books")
    assert response.status_code == 200
    books = response.get_json()
    assert len(books) == 2
    

def test_search_book(client):
    """Tests software book search function"""
    client.post(
        "/books",
        json = {"title": "booktest", "author": "greg", "isbn": '4554', "total_copies": 2}
    )

    search_result = client.get("/books?search=booktest")
    assert search_result.status_code == 200
    result = search_result.get_json()
    assert len(result) >= 1
    assert result[0]["title"] == "booktest"
    

def test_get_book_by_id(client):
    """Tests searching specific book by its ID"""
    client.post(
        "/books",
        json = {"title": "big book", "author": " author", "isbn": '4545', "total_copies": 2}
    )

    response = client.get("/books/1")
    assert response.status_code == 200
    book = response.get_json()
    assert book["id"] == 1
    assert book["title"] == "big book"

def test_update_book(client):
    """Tests updating book information/records"""
    client.post(
        "/books",
        json = {"title": "old title", "author": " author", "isbn": '1234', "total_copies": 2}
    )

    update_payload = {"title": "new title", "author": "author", "isbn": '1234', "total_copies": 2}
    response = client.put("/books/1", json = update_payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data["title"] == "new title"
    assert data["total_copies"] == 2

def  test_delete_book(client):
    """Tests deleting a book record"""
    client.post(
        "/books", 
        json = {"title": "delete", "author": " temp", "isbn": '4321', "total_copies": 2}
    )

    response = client.delete("/books/1")
    assert response.status_code == 204

    check = client.get("/books/1")
    assert check.status_code == 404


def test_checkout_book(client):
    """Tests checkout out book to member"""
    client.post(
            "/books", 
            json = {"title": "bookOne", "author": "Timmy Turner", "isbn": '9878', "total_copies": 1}
        )
    
    client.post(
        "/members",
        json = {"name": "Jerry", "email": "jerry@gmail.com"}
    )

    loan_payload = {"book_id":1, "member_id": 1}
    response = client.post("/loans", json = loan_payload)
    assert response.status_code == 201
    loan_data = response.get_json()
    assert loan_data["book_id"] == 1
    assert loan_data["member_id"] == 1
    assert loan_data["return_date"] is None

    book_result = client.get("/books/1")
    assert book_result.get_json()["available_copies"] == 0

def test_display_loans(client):
    """Tests listing past and current loans"""
    client.post(
        "/books",
        json = {"title": "Cats", "author": "Turner", "isbn": '888', "total_copies": 1}
    )

    client.post(
        "/members",
        json = {"name": "Jerry", "email": "jerry@gmail.com"}
    )

    client.post(
        "/loans",
        json = {"book_id": 1, "member_id": 1}
    )

    response = client.get("/loans")
    assert response.status_code == 200
    loans = response.get_json()
    assert len(loans) == 1
    assert loans[0]["id"] == 1

def test_return_loan(client):
    """Tests returning loaned book"""
    client.post(
        "/books",
        json = {"title": "book to return", "author": "rehtua", "isbn": '000', "total_copies": 1}
    )

    client.post(
        "/members",
        json = {"name": "sam", "email": "sam@gmail.com"}
    )

    client.post(
        "/loans",
        json = {"book_id": 1, "member_id": 1}
    )

    response = client.put("/loans/1/return")
    assert response.status_code == 200
    loan_data = response.get_json()
    assert loan_data["return_date"]

    book_result = client.get("/books/1")
    assert book_result.get_json()["available_copies"] == 1

def test_renew_loan(client):
    """Tests renewing an active loan to extend its due date"""
    client.post(
        "/books",
        json = {"title": "book to renew", "author": "AUTHOR", "isbn": '020', "total_copies": 1}
    )
    
    client.post(
        "/members",
        json = {"name": "samuel", "email": "samuel@gmail.com"}
    )

    client.post(
        "/loans",
        json = {"book_id": 1, "member_id": 1}
    )

    response = client.put("/loans/1/renew")
    assert response.status_code == 200
    loan_data = response.get_json()
    assert "due_date" in loan_data

def test_get_member_loans(client):
    """Tests retrieving all loans for a specific member"""
    client.post(
        "/members",
        json = {"name": "jimmy", "email": "jimmy@gmail.com"}
    )
    
    client.post(
        "/books",
        json = {"title": "121212", "author": "212121", "isbn": "8888", "total_copies": 2}
    )
    
    client.post(
        "/loans",
        json = {"book_id": 1, "member_id": 1}
    )
    
    response = client.get("/members/1/loans")
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) >= 1
    assert data[-1]["member_id"] == 1
    assert data[-1]["book_id"] == 1

def test_get_overdue_loans(client):
    """Tests retrieving overdue loans list"""
    response = client.get("/loans/overdue")
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)