class Keepalive < Formula
  desc "Menu bar app — keep macOS awake on schedule"
  homepage "https://github.com/skozar/keepalive"
  version "0.6.0"
  url "https://github.com/skozar/keepalive/releases/download/v#{version}/Keepalive-#{version}.zip"
  sha256 "8061ab3d376b926e8df6de028af0d3eea1f1d77ed3e5f6a0c04bfaa9c30a5716"

  depends_on "keepalive-cli"

  def install
    prefix.install "Keepalive.app"
  end

  def post_install
    system "ln", "-sf", prefix/"Keepalive.app", "/Applications/Keepalive.app"
  end

  def caveats
    <<~EOS
      Keepalive.app has been symlinked to /Applications/Keepalive.app.
      Launch it from Spotlight or Launchpad.

      Settings are stored in ~/.config/keepalive/settings.json
      and survive reinstalls — you only need to configure once.

      IMPORTANT: The keepalive-cli binary must have Accessibility
      permission for mouse jiggle to work:
        System Settings → Privacy & Security → Accessibility
        Add: /opt/homebrew/bin/keepalive-cli
    EOS
  end
end
