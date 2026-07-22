APP_NAME = keepalive
BINARY = dist/$(APP_NAME)
GUI_NAME = Keepalive
GUI_APP = dist/$(GUI_NAME).app
GUI_ZIP = dist/$(GUI_NAME)-$(VERSION).zip
FORMULA = Formula/$(APP_NAME).rb
UI_FORMULA = Formula/keepalive-ui.rb
TAP_DIR = $(HOME)/Projects/pets/homebrew-tap
PDM = pdm

.PHONY: all dev test build gui clean release

all: build

dev:
	$(PDM) install --dev

test:
	$(PDM) run pytest -v

build: test
	$(PDM) run pyinstaller --onefile --name $(APP_NAME) src/keepalive/__main__.py

gui:
	rm -rf dist/$(GUI_NAME) dist/$(GUI_NAME).app
	$(PDM) run pyinstaller --windowed --name "$(GUI_NAME)" \
		--add-data "src/gui/assets:assets" \
		src/gui/__main__.py
	@$(PDM) run python -c "import plistlib; p=plistlib.load(open('$(GUI_APP)/Contents/Info.plist','rb')); p['LSUIElement']=True; plistlib.dump(p, open('$(GUI_APP)/Contents/Info.plist','wb'))"

clean:
	rm -rf build dist *.spec .pytest_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; true

release:
	@[ "${VERSION}" ] || ( echo "Usage: make release VERSION=0.3.0"; exit 1 )
	@[ -d "$(TAP_DIR)" ] || ( echo "Tap not found at $(TAP_DIR). Clone it: git clone git@github.com:skozar/homebrew-tap.git $(TAP_DIR)"; exit 1 )
	@echo "============================================"
	@echo "🔨 Step 1/7: Running tests..."
	@$(MAKE) test
	@echo "🔨 Step 2/7: Building CLI binary..."
	@$(MAKE) build
	@echo "🔨 Step 3/7: Building GUI .app..."
	@$(MAKE) gui
	@echo "📦 Step 4/7: Zipping .app..."
	@cd dist && zip -r $(GUI_NAME)-$(VERSION).zip "$(GUI_NAME).app"
	@echo "🏷️  Step 5/7: Tagging and pushing..."
	@git tag v$(VERSION) 2>/dev/null; git push origin v$(VERSION) 2>/dev/null || true
	@git tag keepalive-ui-v$(VERSION) 2>/dev/null; git push origin keepalive-ui-v$(VERSION) 2>/dev/null || true
	@echo "🚀 Step 6/7: Creating GitHub releases..."
	@NOTES_FILE=/tmp/keepalive-release-notes-$(VERSION).md; \
	awk '/^## v$(VERSION) /{flag=1;next} /^## v/{flag=0} flag' CHANGELOG.md > $$NOTES_FILE; \
	[ -s $$NOTES_FILE ] || echo "v$(VERSION)" > $$NOTES_FILE; \
	CLI_SHA=$$(shasum -a 256 $(BINARY) | cut -d' ' -f1); \
	GUI_SHA=$$(shasum -a 256 dist/$(GUI_NAME)-$(VERSION).zip | cut -d' ' -f1); \
	echo "CLI sha256: $$CLI_SHA"; \
	echo "UI  sha256: $$GUI_SHA"; \
	echo "📝 Updating formulas..."; \
	sed -i '' "s/version \".*\"/version \"$(VERSION)\"/" $(FORMULA); \
	sed -i '' "s/sha256 \".*\"/sha256 \"$$CLI_SHA\"/" $(FORMULA); \
	sed -i '' "s/version \".*\"/version \"$(VERSION)\"/" $(UI_FORMULA); \
	sed -i '' "s|keepalive-ui-v[0-9.]*/Keepalive-[0-9.]*.zip|keepalive-ui-v$(VERSION)/Keepalive-$(VERSION).zip|" $(UI_FORMULA); \
	sed -i '' "s/sha256 \".*\"/sha256 \"$$GUI_SHA\"/" $(UI_FORMULA); \
	sed -i '' 's/__version__ = ".*"/__version__ = "$(VERSION)"/' src/keepalive/__init__.py; \
	sed -i '' 's/^version = ".*"/version = "$(VERSION)"/' pyproject.toml; \
	git add $(FORMULA) $(UI_FORMULA) CHANGELOG.md pyproject.toml src/keepalive/__init__.py; \
	git commit -m "v$(VERSION): update formulas" || true; \
	git push origin main; \
	gh release create v$(VERSION) $(BINARY) --title "v$(VERSION)" --notes-file $$NOTES_FILE || true; \
	gh release create keepalive-ui-v$(VERSION) dist/$(GUI_NAME)-$(VERSION).zip --title "Keepalive UI v$(VERSION)" --notes-file $$NOTES_FILE || true; \
	rm -f $$NOTES_FILE; \
	echo "📋 Step 7/7: Updating homebrew-tap..."; \
	cp $(FORMULA) $(TAP_DIR)/Formula/; \
	cp $(UI_FORMULA) $(TAP_DIR)/Formula/; \
	cd $(TAP_DIR) && git add . && git commit -m "keepalive v$(VERSION)" || true && git push origin main; \
	echo "✅ Release v$(VERSION) complete."
