import sys


def test_mapeditor_importable(monkeypatch, capsys):
    """At least catch import errors!"""
    from rgkit.mapeditor import main
    # empty command line args
    monkeypatch.setattr(sys, 'argv', sys.argv[:1])
    main()
    out, err = capsys.readouterr()
    assert 'usage: ' in out


def test_other_imports():
    from rgkit.render.robotsprite import RobotSprite
    from rgkit.render.render import Render
    from rgkit.render.highlightsprite import HighlightSprite
    from rgkit.rgcurses import RGCurses
    # prevent flake8 complaining
    (RobotSprite, Render, HighlightSprite, RGCurses)
