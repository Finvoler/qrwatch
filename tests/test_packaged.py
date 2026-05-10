from qrwatch import packaged


def test_packaged_entrypoint_defaults_to_tray_and_local_config(monkeypatch):
    calls = []

    def fake_cli_main(argv, **kwargs):
        calls.append((argv, kwargs))
        return 0

    monkeypatch.setattr(packaged, "cli_main", fake_cli_main)

    assert packaged.main([]) == 0
    assert calls == [
        (
            [],
            {
                "use_default_config_file": True,
                "create_default_config": True,
                "default_tray": True,
            },
        )
    ]


def test_packaged_entrypoint_passes_cli_arguments(monkeypatch):
    calls = []

    def fake_cli_main(argv, **kwargs):
        calls.append((argv, kwargs))
        return 0

    monkeypatch.setattr(packaged, "cli_main", fake_cli_main)

    assert packaged.main(["--capture-once", "--monitor", "0"]) == 0
    assert calls[0][0] == ["--capture-once", "--monitor", "0"]
    assert calls[0][1]["default_tray"] is True
