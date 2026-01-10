import pytest
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from apps.accounts.models.cash_flow_view import CashFlowGroup, CashFlowResult, CashFlowView
from apps.accounts.models.categories import Category


@pytest.mark.django_db
def test_cash_flow_view_creation() -> None:
    """Test creating a cash flow view."""
    user = User.objects.create_user(username="testuser", password="testpass")
    view = CashFlowView.objects.create(user=user, name="Test View")
    assert view.name == "Test View"
    assert view.user == user
    assert view.id is not None


@pytest.mark.django_db
def test_cash_flow_view_unique_name_per_user() -> None:
    """Test that cash flow view names must be unique per user."""
    user = User.objects.create_user(username="testuser", password="testpass")
    CashFlowView.objects.create(user=user, name="Test View")

    with pytest.raises(Exception):  # IntegrityError or ValidationError
        CashFlowView.objects.create(user=user, name="Test View")


@pytest.mark.django_db
def test_cash_flow_view_same_name_different_users() -> None:
    """Test that different users can have views with the same name."""
    user1 = User.objects.create_user(username="user1", password="testpass")
    user2 = User.objects.create_user(username="user2", password="testpass")
    view1 = CashFlowView.objects.create(user=user1, name="Test View")
    view2 = CashFlowView.objects.create(user=user2, name="Test View")

    assert view1.id != view2.id
    assert view1.name == view2.name


@pytest.mark.django_db
def test_cash_flow_group_creation() -> None:
    """Test creating a cash flow group."""
    user = User.objects.create_user(username="testuser", password="testpass")
    view = CashFlowView.objects.create(user=user, name="Test View")
    group = CashFlowGroup.objects.create(
        cash_flow_view=view, name="Revenue", position=1
    )
    assert group.name == "Revenue"
    assert group.position == 1
    assert group.cash_flow_view == view


@pytest.mark.django_db
def test_cash_flow_group_with_categories() -> None:
    """Test adding categories to a cash flow group."""
    user = User.objects.create_user(username="testuser", password="testpass")
    view = CashFlowView.objects.create(user=user, name="Test View")
    category1 = Category.objects.create(
        user=user, name="Sales", transaction_type=Category.TransactionType.INCOME
    )
    category2 = Category.objects.create(
        user=user, name="Services", transaction_type=Category.TransactionType.INCOME
    )

    group = CashFlowGroup.objects.create(
        cash_flow_view=view, name="Revenue", position=1
    )
    group.categories.add(category1, category2)

    assert group.categories.count() == 2
    assert category1 in group.categories.all()
    assert category2 in group.categories.all()


@pytest.mark.django_db
def test_cash_flow_group_position_validation() -> None:
    """Test that groups cannot have duplicate positions within the same view."""
    user = User.objects.create_user(username="testuser", password="testpass")
    view = CashFlowView.objects.create(user=user, name="Test View")
    CashFlowGroup.objects.create(cash_flow_view=view, name="Group 1", position=1)

    group2 = CashFlowGroup(cash_flow_view=view, name="Group 2", position=1)
    with pytest.raises(ValidationError):
        group2.full_clean()


@pytest.mark.django_db
def test_cash_flow_result_creation() -> None:
    """Test creating a cash flow result."""
    user = User.objects.create_user(username="testuser", password="testpass")
    view = CashFlowView.objects.create(user=user, name="Test View")
    result = CashFlowResult.objects.create(
        cash_flow_view=view, name="Gross Margin", position=1
    )
    assert result.name == "Gross Margin"
    assert result.position == 1
    assert result.cash_flow_view == view


@pytest.mark.django_db
def test_cash_flow_result_position_validation() -> None:
    """Test that results cannot have duplicate positions within the same view."""
    user = User.objects.create_user(username="testuser", password="testpass")
    view = CashFlowView.objects.create(user=user, name="Test View")
    CashFlowResult.objects.create(cash_flow_view=view, name="Result 1", position=1)

    result2 = CashFlowResult(cash_flow_view=view, name="Result 2", position=1)
    with pytest.raises(ValidationError):
        result2.full_clean()


@pytest.mark.django_db
def test_group_and_result_cannot_share_position() -> None:
    """Test that groups and results cannot share the same position."""
    user = User.objects.create_user(username="testuser", password="testpass")
    view = CashFlowView.objects.create(user=user, name="Test View")
    CashFlowGroup.objects.create(cash_flow_view=view, name="Group 1", position=1)

    result = CashFlowResult(cash_flow_view=view, name="Result 1", position=1)
    with pytest.raises(ValidationError):
        result.full_clean()


@pytest.mark.django_db
def test_different_views_can_have_same_positions() -> None:
    """Test that different views can have groups/results with the same positions."""
    user = User.objects.create_user(username="testuser", password="testpass")
    view1 = CashFlowView.objects.create(user=user, name="View 1")
    view2 = CashFlowView.objects.create(user=user, name="View 2")

    group1 = CashFlowGroup.objects.create(
        cash_flow_view=view1, name="Group", position=1
    )
    group2 = CashFlowGroup.objects.create(
        cash_flow_view=view2, name="Group", position=1
    )

    assert group1.position == group2.position
    assert group1.cash_flow_view != group2.cash_flow_view

