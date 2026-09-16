.PHONY: figures ui visual-test ui-check

ui:
	node tools/build_ui.mjs

figures: ui
	node tools/make_figures.mjs

ui-check:
	node tools/build_ui.mjs --check

visual-test: ui-check
	node ui/test-render.cjs
	node tools/validate_tokens.mjs
	node tools/test_ui_contract.mjs
	node tools/test_ui_browser.mjs
	node tools/test_repository_review.mjs