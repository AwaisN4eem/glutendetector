from datetime import datetime, timedelta, timezone


def test_explain_gluten_risk_fallback(client):
    """
    Should work even without Groq by returning a simple explanation string.
    """
    resp = client.post(
        "/api/explain/gluten-risk",
        json={"food_name": "pizza", "gluten_risk": 100, "meal_description": "Pepperoni pizza"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "100" in data["explanation"]


def test_prediction_fallback_not_enough_data(client, test_db_session):
    """
    Prediction endpoint should return a friendly fallback when there's not enough historical data
    or Groq is unavailable.
    """
    from models import Meal

    meal = Meal(
        user_id=1,
        description="Test meal",
        meal_type="dinner",
        timestamp=datetime(2026, 1, 10, tzinfo=timezone.utc) - timedelta(hours=3),
        gluten_risk_score=80,
        contains_gluten=True,
        gluten_sources=["bread"],
        detected_foods=[{"name": "bread"}],
        input_method="text",
    )
    test_db_session.add(meal)
    test_db_session.commit()
    test_db_session.refresh(meal)

    resp = client.get(f"/api/prediction/predict/{meal.id}", params={"user_id": 1})
    assert resp.status_code == 200, resp.text
    data = resp.json()

    # In fallback: confidence should be 0 and prediction should mention insufficient data
    assert data["confidence"] == 0
    assert "Not enough data" in data["prediction"]


