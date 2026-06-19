from app.ai.specialty_router_agent import recommend_specialty


class SpecialtyStub:
    def __init__(self, id, name):
        self.id = id
        self.name = name


class QueryStub:
    def __init__(self, rows):
        self.rows = rows

    def all(self):
        return self.rows

    def order_by(self, *_args, **_kwargs):
        return self

    def first(self):
        return self.rows[0] if self.rows else None


class DBStub:
    def __init__(self):
        self.rows = [
            SpecialtyStub(1, "General Physician"),
            SpecialtyStub(4, "ENT Specialist"),
        ]

    def query(self, _model):
        return QueryStub(self.rows)


def test_specialty_router_ent_or_general_for_throat_cough():
    result = recommend_specialty(
        {"main_symptoms": ["fever", "cough", "sore throat"]},
        {"urgency_level": "soon"},
        DBStub(),
    )
    assert result["recommended_specialty"].name in {"ENT Specialist", "General Physician"}
