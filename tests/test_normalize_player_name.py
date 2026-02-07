import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from player_evaluation.utils import normalize_player_name


def test_diacritics_stripped():
    assert normalize_player_name("Jesús Luzardo") == "Jesus Luzardo"
    assert normalize_player_name("José Ramírez") == "Jose Ramirez"
    assert normalize_player_name("Ronald Acuña Jr.") == "Ronald Acuna"


def test_plain_name_unchanged():
    assert normalize_player_name("Jesus Luzardo") == "Jesus Luzardo"
    assert normalize_player_name("Shohei Ohtani") == "Shohei Ohtani"
    assert normalize_player_name("Jose Ramirez") == "Jose Ramirez"


def test_jr_sr_suffixes_removed():
    assert normalize_player_name("Vladimir Guerrero Jr.") == "Vladimir Guerrero"
    assert normalize_player_name("Fernando Tatis Jr") == "Fernando Tatis"
    assert normalize_player_name("Bobby Witt Jr.") == "Bobby Witt"
    assert normalize_player_name("Ken Griffey Sr.") == "Ken Griffey"


def test_periods_removed():
    assert normalize_player_name("J.D. Martinez") == "JD Martinez"


def test_middle_initials_removed():
    assert normalize_player_name("Luis L. Ortiz") == "Luis Ortiz"
    assert normalize_player_name("Luis Ortiz") == "Luis Ortiz"


def test_apostrophe_removed():
    assert normalize_player_name("Ke'Bryan Hayes") == "KeBryan Hayes"
    assert normalize_player_name("Ryan O'Hearn") == "Ryan OHearn"


def test_non_string_passthrough():
    assert normalize_player_name(None) is None
    assert normalize_player_name(42) == 42
