from clockbind.stats import egba, surveyplan

RO = {"expression": "o_I - rho*p_S + (F_I - F_S)/Q", "fixed": {"Q": 500, "F_I": 0},
      "parameters": {"o_I": {"B": [0, 14.75]}, "rho": {"A": [0, 0.09473]}, "p_S": {"B": [9.2773, 16.8924]}, "F_S": {"D": [8988, 64800]}},
      "label_below": "integration favoured", "breakdown_parameter": "o_I"}


def test_egba_reproduces_published_romania_q500():
    r = egba.run(RO)
    assert r["rungs"][2]["status"] == "NOT IDENTIFIED"
    assert round(r["final"]["low"], 2) == -131.20 and round(r["final"]["high"], 2) == -3.23
    assert abs(r["breakdown"]["value"] - 17.976) < 1e-6


def test_survey_grade_narrows_and_conflict_is_kept():
    spec = {**RO, "parameters": {**RO["parameters"], "o_I": {"B": [0, 14.75], "S": [20, 30]}}}
    r = egba.run(spec)
    assert r["conflicts"] and r["final"]["intervals"]["o_I"] == [0.0, 14.75]


def test_survey_plan_matches_quartile_r():
    s = {"response_rate": .10, "completion_loss": .15, "eligibility": .8, "target_total": 600, "groups": [{"name": "Strong"}, {"name": "Weak"}],
         "papers": [{"name": "P1", "components": [{"type": "conjoint", "levels_max": 4, "tasks": 10, "alternatives": 2}, {"type": "two_group", "d": 0.3}]},
                    {"name": "P2", "components": [{"type": "cfa", "items": 15, "factors": 3, "per_group": True}, {"type": "regression", "f2": 0.02, "predictors": 1, "total_predictors": 10}]},
                    {"name": "P3", "components": [{"type": "logistic", "predictors": 8, "event_rate": 0.3, "epv": 20}]}]}
    r = surveyplan.plan(s)
    ns = [c["n"] for p in r["papers"] for c in p["components"]]
    assert ns == [100, 352, 145, 395, 534] and r["total_completes"] == 600 and r["total_invitations"] == 8824


def test_egba_time_worked_example():
    import json, os
    from clockbind.stats import egba_time
    spec = json.load(open(os.path.join(os.path.dirname(__file__), "egba_time_example.json")))
    r = egba_time.run(spec)
    labels = [x["label"] for x in r["routes"]]
    assert labels == ["surely on time", "undetermined", "surely on time", "surely late", "surely late", "not usable", "not identified"]
    assert r["routes"][0]["latency"] == [8.0, 24.0]  # approval S 1-2 weeks intersected with A 5-21 days
    assert abs(r["share_usable_in_time"]["lower"] - 2 / 7) < 1e-12 and abs(r["share_usable_in_time"]["upper"] - 4 / 7) < 1e-12
    assert len(r["conflicts"]) == 1  # pending route elapsed beyond reported upper bound
