class KeepaliveUi < Formula
  desc "Menu bar controller for the keepalive activity agent"
  homepage "https://github.com/skozar/keepalive"
  version "0.1.1"
  url "https://github.com/skozar/keepalive/releases/download/keepalive-ui-v0.1.1/Keepalive-0.1.1.zip"
  sha256 "b91e3edac32e69eb10c30baf2290d3b1a6881447b7f455f705475f88901ca079"
  license "MIT"

  depends_on "keepalive"

  def install
    # Zip unpacks Keepalive.app/ — we're already inside it.
    (prefix/"Keepalive.app").install Dir["*"]
  end

  def post_install
    target = Pathname("/Applications/Keepalive.app")
    target.unlink if target.exist? || target.symlink?
    FileUtils.ln_sf prefix/"Keepalive.app", target
  end

  def caveats
    <<~EOS
      Keepalive.app has been symlinked to /Applications/Keepalive.app.
      Launch it from Spotlight or Launchpad.

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
