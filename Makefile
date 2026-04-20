.PHONY: lint lint-check test test-linux testpub gui-test

lint:
	uv run ruff format
	uv run ruff check --fix

lint-check:
	uv run ruff format --diff
	uv run ruff check

test:
	if [ -n "$(GITHUB_RUN_ID)" ]; then \
		uv run pytest --cov --cov-report=xml --junitxml=junit.xml -o junit_family=legacy; \
	else \
		uv run python -m pytest --cov; \
	fi

test-linux:
	docker build -f tests/Dockerfile.linux-test -t pyautogui-next-test-linux .
	docker run --rm --init -e PYAUTOGUI_LOCATE_BUTTON_IMAGE=linux-docker pyautogui-next-test-linux

testpub:
	rm -fr dist
	uv build
	uv run twine upload --repository testpypi dist/*


test-gui: export PYAUTOGUI_RUN_GUI_TESTS=1
test-gui: test

test-docker-gui: export PYAUTOGUI_GUI_TEST_BACKEND=docker
test-docker-gui: test-gui
