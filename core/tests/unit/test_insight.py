from src.insight import decide_insight
from src.similarity import Match

MATCH = Match(event_id="evt_prev", similarity=0.9)


def test_no_insight_when_depth_level_is_minimo():
    preferences = {"depth_level": "minimo", "interests": []}
    result = decide_insight([MATCH], preferences, current_text="robotica", matched_text_by_event_id={})
    assert result is None


def test_no_insight_when_no_matches():
    preferences = {"depth_level": "equilibrato", "interests": []}
    result = decide_insight([], preferences, current_text="ciao", matched_text_by_event_id={})
    assert result is None


def test_high_priority_when_match_is_of_interest():
    preferences = {"depth_level": "equilibrato", "interests": ["robotica"]}
    result = decide_insight(
        [MATCH],
        preferences,
        current_text="oggi ho lavorato al braccio robotico",
        matched_text_by_event_id={"evt_prev": "appunti sulla robotica"},
    )
    assert result.priority == "alta"


def test_normal_priority_when_match_is_not_of_interest():
    preferences = {"depth_level": "equilibrato", "interests": ["robotica"]}
    result = decide_insight(
        [MATCH],
        preferences,
        current_text="lista della spesa",
        matched_text_by_event_id={"evt_prev": "altra lista della spesa"},
    )
    assert result.priority == "normale"
