from datetime import date, timedelta
from app import store


# Test for due date boundary
def test_fine_on_due_date(client):
    client.post('/books', json={
        'title': 'test', 'author': 'testing', 'isbn': 'test'
    })
    client.post('/members', json={
        'name': 'test', 'email': 'test@example.com'
    })
    client.post('/loans', json={'book_id': 1, 'member_id': 1})

    store.loans[1].due_date = date.today()

    response = client.get('/loans/1/fine')
    assert response.status_code == 200
    assert response.get_json()['fine_amount'] == 0


# Test for overdue fine
def test_overdue_fine(client):
    client.post('/books', json={
        'title': 'test', 'author': 'testing', 'isbn': 'test'
    })
    client.post('/members', json={
        'name': 'test', 'email': 'test@example.com'
    })
    client.post('/loans', json={'book_id': 1, 'member_id': 1})

    store.loans[1].due_date = date.today() - timedelta(days=4)

    response = client.get('/loans/1/fine')
    assert response.status_code == 200
    assert response.get_json()['fine_amount'] == 1.00


# Test for fine stopping after return
def test_fine_stops_at_return(client):
    client.post('/books', json={
        'title': 'test', 'author': 'testing', 'isbn': 'test'
    })
    client.post('/members', json={
        'name': 'test', 'email': 'test@example.com'
    })
    client.post('/loans', json={'book_id': 1, 'member_id': 1})

    store.loans[1].due_date = date.today() - timedelta(days=5)
    store.loans[1].return_date = date.today() - timedelta(days=3)

    response = client.get('/loans/1/fine')
    assert response.status_code == 200
    assert response.get_json()['fine_amount'] == 0.50

# Test for creating a reservation
def test_create_reservation(client):
    client.post('/books', json={
        'title': 'test',
        'author': 'testing',
        'isbn': 'test',
        'total_copies': 0
    })
    client.post('/members', json={
        'name': 'test', 'email': 'test@example.com'
    })

    response = client.post('/reservations', json={
        'book_id': 1, 'member_id': 1
    })

    assert response.status_code == 201
    reservation = response.get_json()
    assert reservation['book_id'] == 1
    assert reservation['member_id'] == 1
    assert reservation['fulfilled'] is False
    assert reservation['reservation_date'] == date.today().isoformat()
    assert client.get('/reservations').get_json() == [reservation]


# Test for listing and filtering reservations
def test_list_reservations(client):
    client.post('/books', json={
        'title': 'test',
        'author': 'testing',
        'isbn': 'test',
        'total_copies': 0
    })
    client.post('/members', json={
        'name': 'test', 'email': 'test@example.com'
    })
    client.post('/members', json={
        'name': 'testing', 'email': 'testing@example.com'
    })

    first = client.post('/reservations', json={
        'book_id': 1, 'member_id': 1
    }).get_json()
    second = client.post('/reservations', json={
        'book_id': 1, 'member_id': 2
    }).get_json()

    response = client.get('/reservations')
    assert response.status_code == 200
    assert response.get_json() == [first, second]
    assert client.get('/reservations?member_id=2').get_json() == [second]
    assert client.get('/reservations?book_id=1').get_json() == [first, second]
    assert client.get('/reservations?book_id=999').get_json() == []


# Test for reservation with a nonexistent member
def test_reservation_missing_member(client):
    client.post('/books', json={
        'title': 'test',
        'author': 'testing',
        'isbn': 'test',
        'total_copies': 0
    })

    response = client.post('/reservations', json={
        'book_id': 1, 'member_id': 999
    })

    assert response.status_code == 404
    assert response.get_json()['error'] == 'Member not found'
    assert client.get('/reservations').get_json() == []