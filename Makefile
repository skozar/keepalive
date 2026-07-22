APP_NAME = keepalive
BINARY = dist/$(APP_NAME)
GUI_NAME = Keepalive
GUI_APP = dist/$(GUI_NAME).app
FORMULA = Formula/$(APP_NAME).rb
UI_FORMULA = Formula/keepalive-ui.rb
TAP_DIR = $(HOME)/Projects/pets/homebrew-tap
PDM = pdm

.PHONY: all dev test build gui clean release release-ui

all: build

dev:
	$(PDM) install --dev

test:
	$(PDM) run pytest -v

build: test
	$(PDM) run pyinstaller --onefile --name $(APP_NAME) src/keepalive/__main__.py

gui:
	rm -rf dist/$(GUI_NAME) dist/$(GUI_NAME).app
	$(PDM) run pyinstaller --windowed --name "$(GUI_NAME)" src/gui/__main__.py
	@$(PDM) run python -c "import plistlib; p=plistlib.load(open('$(GUI_APP)/Contents/Info.plist','rb')); p['LSUIElement']=True; plistlib.dump(p, open('$(GUI_APP)/Contents/Info.plist','wb'))"

clean:
	rm -rf build dist *.spec .pytest_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; true

release:
	@[ "${VERSION}" ] || ( echo "Usage: make release VERSION=0.2.0"; exit 1 )
	@[ -d "$(TAP_DIR)" ] || ( echo "Tap not found at $(TAP_DIR). Clone it: git clone git@github.com:skozar/homebrew-tap.git $(TAP_DIR)"; exit 1 )
	@echo "🔨 Building..."
	@$(MAKE) build
	@SHA=$$(shasum -a 256 $(BINARY) | cut -d' ' -f1); \
	echo "📦 sha256: $$SHA"; \
	echo "📝 Updating formula (v$(VERSION), $$SHA)..."; \
	sed -i '' "s/version \".*\"/version \"$(VERSION)\"/" $(FORMULA); \
	sed -i '' "s/sha256 \".*\"/sha256 \"$$SHA\"/" $(FORMULA); \
	echo "📤 Committing and pushing formula update..."; \
	git add $(FORMULA); \
	git commit -m "v$(VERSION): update formula" || true; \
	git push origin main; \
	echo "🏷️  Tagging v$(VERSION)..."; \
	git tag v$(VERSION); \
	git push origin v$(VERSION); \
	echo "🚀 Creating GitHub release..."; \
	gh release create v$(VERSION) $(BINARY) --title "v$(VERSION)" --notes "Release v$(VERSION)" || true; \
	echo "📋 Updating homebrew-tap..."; \
	cp $(FORMULA) $(TAP_DIR)/Formula/; \
	cd $(TAP_DIR) && git add . && git commit -m "keepalive v$(VERSION)" || true && git push origin main; \
	echo "✅ Release v$(VERSION) complete."

release-ui:
	@[ "${VERSION}" ] || ( echo "Usage: make release-ui VERSION=0.1.0"; exit 1 )
	@[ -d "$(TAP_DIR)" ] || ( echo "Tap not found at $(TAP_DIR). Clone it: git clone git@github.com:skozar/homebrew-tap.git $(TAP_DIR)"; exit 1 )
	@echo "🔨 Building GUI..."
	@$(MAKE) gui
	@echo "📦 Zipping .app..."
	@cd dist && zip -r $(GUI_NAME)-$(VERSION).zip "$(GUI_NAME).app"
	@SHA=$$(shasum -a 256 dist/$(GUI_NAME)-$(VERSION).zip | cut -d' ' -f1); \
	echo "📦 sha256: $$SHA"; \
	echo "📝 Updating UI formula (v$(VERSION), $$SHA)..."; \
	sed -i '' "s/version \".*\"/version \"$(VERSION)\"/" $(UI_FORMULA); \
	sed -i '' "s/sha256 \".*\"/sha256 \"$$SHA\"/" $(UI_FORMULA); \
	echo "📤 Committing and pushing formula update..."; \
	git add $(UI_FORMULA); \
	git commit -m "keepalive-ui v$(VERSION): update formula" || true; \
	git push origin main; \
	echo "🏷️  Tagging keepalive-ui-v$(VERSION)..."; \
	git tag keepalive-ui-v$(VERSION); \
	git push origin keepalive-ui-v$(VERSION); \
	echo "🚀 Creating GitHub release..."; \
	gh release create keepalive-ui-v$(VERSION) dist/$(GUI_NAME)-$(VERSION).zip --title "Keepalive UI v$(VERSION)" --notes "Menu bar controller for keepalive. v$(VERSION)" || true; \
	echo "📋 Updating homebrew-tap..."; \
	cp $(UI_FORMULA) $(TAP_DIR)/Formula/; \
	cd $(TAP_DIR) && git add . && git commit -m "keepalive-ui v$(VERSION)" || true && git push origin main; \
	echo "✅ Release UI v$(VERSION) complete."
