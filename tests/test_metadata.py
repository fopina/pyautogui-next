import importlib.metadata


def test_package_metadata_obsoletes_original_pyautogui_distribution():
    metadata = importlib.metadata.metadata('pyautogui-next')

    assert metadata.get_all('Obsoletes-Dist') == ['pyautogui']
