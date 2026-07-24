APP_NAME = keepalive-cli
BINARY = dist/$(APP_NAME)/$(APP_NAME)
FORMULA = Formula/$(APP_NAME).rb
TAP_DIR = $(HOME)/Projects/pets/homebrew-tap
PDM = pdm

.PHONY: all dev test build clean release

all: test build

dev:
	$(PDM) install --dev

test:
	$(PDM) run pytest -v

build:
	rm -rf dist/$(APP_NAME)
	$(PDM) run pyinstaller --onedir --name $(APP_NAME) src/keepalive/__main__.py

clean:
	rm -rf build dist *.spec __pycache__ src/**/__pycache__ tests/**/__pycache__

# ── release ──────────────────────────────────────────────────────────────────

release:
	@[ -n "$(VERSION)" ] || (echo "❌ VERSION= required, e.g. make release VERSION=0.7.0" && exit 1)
	@echo "🔨 Step 1/6: Running tests..."
	@$(MAKE) test
	@echo "🔨 Step 2/6: Building CLI binary..."
	@$(MAKE) build
	@echo "📦 Packaging..."
	@cd dist && tar --no-xattrs -czf $(APP_NAME)-$(VERSION).tar.gz "$(APP_NAME)"
	@echo "🏷️  Step 3/6: Tagging..."
	@PREV_TAG=$$(git tag --sort=-version:refname | grep '^v[0-9]' | head -1); \
	echo "Previous tag: $$PREV_TAG"; \
	git log --oneline $$PREV_TAG..HEAD > /tmp/keepalive_changes; \
	NOTES_FILE=$$(mktemp); \
	echo "## Changes" > $$NOTES_FILE; \
	echo '```' >> $$NOTES_FILE; \
	cat /tmp/keepalive_changes >> $$NOTES_FILE; \
	echo '```' >> $$NOTES_FILE; \
	echo "" >> $$NOTES_FILE; \
	echo "[CLI tar.gz → keepalive-cli-$(VERSION).tar.gz](https://github.com/skozar/keepalive/releases/download/v$(VERSION)/keepalive-cli-$(VERSION).tar.gz)" >> $$NOTES_FILE; \
	echo "" >> $$NOTES_FILE; \
	echo "### Install / Upgrade" >> $$NOTES_FILE; \
	echo '```bash' >> $$NOTES_FILE; \
	echo "brew update && brew upgrade keepalive-cli" >> $$NOTES_FILE; \
	echo '```' >> $$NOTES_FILE
	@echo "📝 Step 4/6: Updating formulas..."
	@CLI_SHA=$$(shasum -a 256 dist/$(APP_NAME)-$(VERSION).tar.gz | cut -d' ' -f1); \
	echo "CLI sha256: $$CLI_SHA"; \
	sed -i '' "s/version \".*\"/version \"$(VERSION)\"/" $(FORMULA); \
	sed -i '' "s/sha256 \".*\"/sha256 \"$$CLI_SHA\"/" $(FORMULA); \
	sed -i '' 's/__version__ = ".*"/__version__ = "$(VERSION)"/' src/keepalive/__init__.py; \
	sed -i '' 's/^version = ".*"/version = "$(VERSION)"/' pyproject.toml; \
	git add $(FORMULA) CHANGELOG.md pyproject.toml src/keepalive/__init__.py; \
	git commit -m "v$(VERSION): update formulas" || true; \
	git push origin main;
	@echo "📋 Step 5/6: Creating GitHub Release..."
	@git tag -a v$(VERSION) -m "v$(VERSION)" || true; \
	git push origin v$(VERSION); \
	gh release create v$(VERSION) dist/$(APP_NAME)-$(VERSION).tar.gz \
		--title "v$(VERSION)" --notes-file $$NOTES_FILE || true; \
	rm -f $$NOTES_FILE
	@echo "📋 Step 6/6: Updating homebrew-tap..."
	@cp $(FORMULA) $(TAP_DIR)/Formula/; \
	cd $(TAP_DIR); \
	git add Formula/$(APP_NAME).rb; \
	git commit -m "keepalive-cli v$(VERSION)"; \
	git push origin main
	@echo "✅ Release v$(VERSION) complete."
