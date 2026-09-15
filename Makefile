.PHONY: figures ui visual-test

ui:
	node tools/build_ui.mjs

figures: ui
	node tools/make_figures.mjs

visual-test: ui
	node ui/test-render.cjs
	node tools/validate_tokens.mjs
	node tools/test_ui_contract.mjs
	node tools/test_ui_browser.mjs