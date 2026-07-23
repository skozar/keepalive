class KeepaliveUi < Formula
  desc "Menu bar controller for the keepalive activity agent"
  homepage "https://github.com/skozar/keepalive"
  version "0.5.3"
  url "https://github.com/skozar/keepalive/releases/download/v0.5.3/KeepaliveUI-0.5.3.zip"
  sha256 "ae1bffe6e9e6de3b4b023e7417958656920617b80d515ac5fa0bab5eb0569400"
  license "MIT"

  depends_on "keepalive"

  def install
    (prefix/"Keepalive.app").install Dir["*"]
  end

  def post_install
    app_source = prefix/"Keepalive.app"
    app_target = Pathname("/Applications/Keepalive.app")
    app_target.delete if app_target.exist? || app_target.symlink?
    app_target.make_symlink(app_source)
  end

  def caveats
    <<~EOS
      Keepalive.app has been symlinked to /Applications/Keepalive.app.
      Launch it from Spotlight or Launchpad.

      Settings are stored in ~/.config/keepalive/settings.json
      and survive reinstalls — you only need to configure once.

      IMPORTANT: The keepalive CLI binary must have Accessibility
      permission for mouse jiggle to work:
        System Settings → Privacy & Security → Accessibility
        Add: /opt/homebrew/bin/keepalive
    EOS
  end

  test do
    system "test", "-d", prefix/"Keepalive.app"
  end
end
