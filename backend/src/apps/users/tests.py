import time

import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from apps.users.models import UserNote

NOTE_URL = "/api/v1/users/note/"


def create_authenticated_client(user: User) -> APIClient:
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.mark.django_db
def test_get_note_creates_empty_note_for_authenticated_user() -> None:
    user = User.objects.create_user(username="note_user_get_001", password="testpass")
    client = create_authenticated_client(user)

    response = client.get(NOTE_URL)

    assert response.status_code == 200
    assert response.data["content"] == ""
    assert UserNote.objects.filter(user=user).count() == 1


@pytest.mark.django_db
def test_put_note_persists_non_empty_content() -> None:
    user = User.objects.create_user(username="note_user_put_001", password="testpass")
    client = create_authenticated_client(user)

    response = client.put(NOTE_URL, {"content": "Pay rent on the 5th"}, format="json")

    assert response.status_code == 200
    assert response.data["content"] == "Pay rent on the 5th"
    note = UserNote.objects.get(user=user)
    assert note.content == "Pay rent on the 5th"


@pytest.mark.django_db
def test_put_note_updates_same_row_and_changes_updated_at() -> None:
    user = User.objects.create_user(username="note_user_put_002", password="testpass")
    client = create_authenticated_client(user)

    first_response = client.put(NOTE_URL, {"content": "first note"}, format="json")
    assert first_response.status_code == 200

    first_note = UserNote.objects.get(user=user)
    first_note_id = first_note.id
    first_updated_at = first_note.updated_at

    time.sleep(0.01)
    second_response = client.put(NOTE_URL, {"content": "second note"}, format="json")

    assert second_response.status_code == 200
    updated_note = UserNote.objects.get(user=user)
    assert updated_note.id == first_note_id
    assert updated_note.content == "second note"
    assert updated_note.updated_at > first_updated_at
    assert UserNote.objects.filter(user=user).count() == 1


@pytest.mark.django_db
def test_put_note_allows_empty_content() -> None:
    user = User.objects.create_user(username="note_user_put_003", password="testpass")
    client = create_authenticated_client(user)

    initial_response = client.put(
        NOTE_URL, {"content": "something to clear"}, format="json"
    )
    assert initial_response.status_code == 200

    response = client.put(NOTE_URL, {"content": ""}, format="json")

    assert response.status_code == 200
    assert response.data["content"] == ""
    note = UserNote.objects.get(user=user)
    assert note.content == ""


@pytest.mark.django_db
def test_user_note_isolation_between_users() -> None:
    user_a = User.objects.create_user(username="note_user_a_001", password="testpass")
    user_b = User.objects.create_user(username="note_user_b_001", password="testpass")

    client_a = create_authenticated_client(user_a)
    client_b = create_authenticated_client(user_b)

    response_a_save = client_a.put(NOTE_URL, {"content": "A note"}, format="json")
    response_b_save = client_b.put(NOTE_URL, {"content": "B note"}, format="json")
    assert response_a_save.status_code == 200
    assert response_b_save.status_code == 200

    response_a_get = client_a.get(NOTE_URL)
    response_b_get = client_b.get(NOTE_URL)

    assert response_a_get.status_code == 200
    assert response_b_get.status_code == 200
    assert response_a_get.data["content"] == "A note"
    assert response_b_get.data["content"] == "B note"


@pytest.mark.django_db
def test_note_endpoint_requires_authentication() -> None:
    unauthenticated_client = APIClient()

    get_response = unauthenticated_client.get(NOTE_URL)
    put_response = unauthenticated_client.put(
        NOTE_URL, {"content": "should fail"}, format="json"
    )

    assert get_response.status_code == 401
    assert put_response.status_code == 401
