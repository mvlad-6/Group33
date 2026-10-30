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

