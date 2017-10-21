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
    import rgkit.render.robotsprite
    import rgkit.render.render
    import rgkit.render.highlightsprite
    import rgkit.rgcurses
