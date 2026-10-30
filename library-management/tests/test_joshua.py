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

# Test for creating a member
def test_create_member(client):
    response = client.post('/members', json={
        'name': 'test', 'email': 'test@example.com'
    })

    assert response.status_code == 201
    member = response.get_json()
    assert member['name'] == 'test'
    assert member['email'] == 'test@example.com'
    assert client.get('/members/1').get_json() == member


# Test for listing members
def test_list_members(client):
    client.post('/members', json={
        'name': 'test', 'email': 'test@example.com'
    })
    client.post('/members', json={
        'name': 'testing', 'email': 'testing@example.com'
    })

    response = client.get('/members')
    assert response.status_code == 200
    members = response.get_json()
    assert len(members) == 2
    assert members[0]['name'] == 'test'
    assert members[1]['name'] == 'testing'


# Test for getting a member by ID
def test_get_member(client):
    client.post('/members', json={
        'name': 'test', 'email': 'test@example.com'
    })

    response = client.get('/members/1')
    assert response.status_code == 200
    assert response.get_json()['id'] == 1
    assert response.get_json()['name'] == 'test'
    assert response.get_json()['email'] == 'test@example.com'


# Test for updating a member
def test_update_member(client):
    client.post('/members', json={
        'name': 'test', 'email': 'test@example.com'
    })

    response = client.put('/members/1', json={'name': 'testing'})
    assert response.status_code == 200

    member = client.get('/members/1').get_json()
    assert member['name'] == 'testing'
    assert member['email'] == 'test@example.com'


# Test for deleting a member
def test_delete_member(client):
    client.post('/members', json={
        'name': 'test', 'email': 'test@example.com'
    })

    response = client.delete('/members/1')
    assert response.status_code == 204
    assert client.get('/members').get_json() == []
    assert client.get('/members/1').status_code == 404


# Test for a nonexistent member
def test_missing_member(client):
    response = client.get('/members/999')

    assert response.status_code == 404
    assert response.get_json()['error'] == 'Member not found'

# Test for stopping another member from taking a reserved book
def test_reserved_book_blocks_other_member(client):
    client.post('/books', json={
        'title': 'test', 'author': 'testing', 'isbn': 'test'
    })
    client.post('/members', json={'name': 'test', 'email': 'test@example.com'})
    client.post('/members', json={'name': 'testing', 'email': 'testing@example.com'})
    client.post('/loans', json={'book_id': 1, 'member_id': 1})
    client.post('/reservations', json={'book_id': 1, 'member_id': 2})
    client.put('/loans/1/return')

    response = client.post('/loans', json={'book_id': 1, 'member_id': 1})
    assert response.status_code == 409
    assert response.get_json()['error'] == 'Book reserved for another member'
    assert client.get('/books/1').get_json()['available_copies'] == 1
    assert len(client.get('/loans').get_json()) == 1
    assert client.get('/reservations').get_json()[0]['fulfilled'] is False


# Test for fulfilling reservations in order
def test_reserved_book_checkout_fulfills_reservation(client):
    client.post('/books', json={
        'title': 'test', 'author': 'testing', 'isbn': 'test'
    })
    client.post('/members', json={'name': 'test', 'email': 'test@example.com'})
    client.post('/members', json={'name': 'testing', 'email': 'testing@example.com'})
    client.post('/loans', json={'book_id': 1, 'member_id': 1})
    client.post('/reservations', json={'book_id': 1, 'member_id': 2})
    client.post('/reservations', json={'book_id': 1, 'member_id': 1})
    client.put('/loans/1/return')

    response = client.post('/loans', json={'book_id': 1, 'member_id': 2})
    assert response.status_code == 201
    assert response.get_json()['member_id'] == 2
    assert client.get('/books/1').get_json()['available_copies'] == 0
    reservations = client.get('/reservations').get_json()
    assert reservations[0]['fulfilled'] is True
    assert reservations[1]['fulfilled'] is False

    client.put('/loans/2/return')
    response = client.post('/loans', json={'book_id': 1, 'member_id': 1})
    assert response.status_code == 201
    assert client.get('/reservations').get_json()[1]['fulfilled'] is True
    assert len(client.get('/loans').get_json()) == 3


# Test for keeping a reservation waiting when no copy is available
def test_reserved_book_needs_available_copy(client):
    client.post('/books', json={
        'title': 'test', 'author': 'testing', 'isbn': 'test', 'total_copies': 0
    })
    client.post('/members', json={'name': 'test', 'email': 'test@example.com'})
    client.post('/reservations', json={'book_id': 1, 'member_id': 1})

    response = client.post('/loans', json={'book_id': 1, 'member_id': 1})
    assert response.status_code == 409
    assert response.get_json()['error'] == 'No copies available'
    assert client.get('/books/1').get_json()['available_copies'] == 0
    assert client.get('/loans').get_json() == []
    assert client.get('/reservations').get_json()[0]['fulfilled'] is False
