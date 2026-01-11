from datetime import datetime, timedelta, timezone


def _seed_meals_and_symptoms(db, user_id: int, start: datetime, days: int = 20):
    """Insert deterministic data with a strong same-day gluten→symptom relationship."""
    from models import Meal, Symptom

    for i in range(days):
        ts_meal = start + timedelta(days=i, hours=12)
        # Alternate low/high gluten to produce clear signal
        is_high = (i % 2 == 0)
        gluten = 90.0 if is_high else 5.0

        db.add(
            Meal(
                user_id=user_id,
                description="Demo meal high gluten" if is_high else "Demo meal low gluten",
                meal_type="lunch",
                timestamp=ts_meal,
                gluten_risk_score=gluten,
                contains_gluten=is_high,
                gluten_sources=["bread"] if is_high else None,
                detected_foods=[{"name": "bread"}] if is_high else [{"name": "rice"}],
                input_method="text",
            )
        )

        # Symptom on same day; severity correlates with gluten level
        ts_sym = start + timedelta(days=i, hours=15)
        severity = 8.0 if is_high else 2.0
        db.add(
            Symptom(
                user_id=user_id,
                symptom_type="bloating",
                description="Bloating after eating",
                severity=severity,
                timestamp=ts_sym,
                time_context="3 hours after eating",
                input_method="text",
                sentiment_score=-0.5,
                extracted_symptoms=[{"type": "bloating", "mention": "bloating"}],
            )
        )

    db.commit()


def test_correlation_includes_metadata(client, test_db_session):
    """
    UI wants these fields:
    - start_date/end_date
    - total_meals/total_symptoms
    - p_value
    """
    end = datetime(2026, 1, 10, tzinfo=timezone.utc)
    start = end - timedelta(days=30)
    _seed_meals_and_symptoms(test_db_session, user_id=1, start=start, days=20)

    resp = client.get(
        "/api/analysis/correlation",
        params={
            "user_id": 1,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
        },
    )
    assert resp.status_code == 200, resp.text

    data = resp.json()
    assert data["total_meals"] >= 20
    assert data["total_symptoms"] >= 20
    assert data["start_date"] is not None
    assert data["end_date"] is not None
    assert data["p_value"] is not None
    assert 0 <= data["correlation_score"] <= 100


def test_generate_report_creates_report_row(client, test_db_session):
    end = datetime(2026, 1, 10, tzinfo=timezone.utc)
    start = end - timedelta(days=90)
    _seed_meals_and_symptoms(test_db_session, user_id=1, start=start, days=35)

    resp = client.post("/api/analysis/generate-report", params={"user_id": 1, "weeks": 12})
    assert resp.status_code == 201, resp.text
    report = resp.json()

    # Basic shape checks (what the UI needs)
    assert report["id"] is not None
    assert report["start_date"] is not None
    assert report["end_date"] is not None
    assert report["total_meals_logged"] >= 10
    assert report["total_symptoms_logged"] >= 10
    assert report["correlation_score"] is not None
    assert report["confidence_level"] is not None


