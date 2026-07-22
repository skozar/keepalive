APP_NAME = keepalive
VENV = venv
BINARY = dist/$(APP_NAME)
FORMULA = Formula/$(APP_NAME).rb
TAP_DIR = $(HOME)/Projects/pets/homebrew-tap

.PHONY: all build clean release

all: build

build: $(BINARY)

$(BINARY): keepalive.py
	$(VENV)/bin/pip install -q pyinstaller
	$(VENV)/bin/pyinstaller --onefile --name $(APP_NAME) keepalive.py

clean:
	rm -rf build dist *.spec

release:
	@[ "${VERSION}" ] || ( echo "Usage: make release VERSION=0.2.0"; exit 1 )
	@[ -d "$(TAP_DIR)" ] || ( echo "Tap not found at $(TAP_DIR). Clone it: git clone git@github.com:skozar/homebrew-tap.git $(TAP_DIR)"; exit 1 )
	@echo "🔨 Building..."
	@$(MAKE) --no-print-directory build
	@echo "📦 Computing sha256..."
	$(eval SHA := $(shell shasum -a 256 $(BINARY) | cut -d' ' -f1))
	@echo "📝 Updating formula (v$(VERSION), sha256=$(SHA))..."
	@sed -i '' "s/version \".*\"/version \"$(VERSION)\"/" $(FORMULA)
	@sed -i '' "s/sha256 \".*\"/sha256 \"$(SHA)\"/" $(FORMULA)
	@echo "📤 Committing and pushing formula update..."
	git add $(FORMULA)
	git commit -m "v$(VERSION): update formula" || true
	git push origin main
	@echo "🏷️  Tagging v$(VERSION)..."
	git tag v$(VERSION)
	git push origin v$(VERSION)
	@echo "🚀 Creating GitHub release..."
	gh release create v$(VERSION) $(BINARY) --title "v$(VERSION)" --notes "Release v$(VERSION)" || true
	@echo "📋 Updating homebrew-tap..."
	cp $(FORMULA) $(TAP_DIR)/Formula/
	cd $(TAP_DIR) && git add . && git commit -m "keepalive v$(VERSION)" || true && git push origin main
	@echo "✅ Release v$(VERSION) complete."
