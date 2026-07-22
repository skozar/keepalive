class KeepaliveUi < Formula
  desc "Menu bar controller for the keepalive activity agent"
  homepage "https://github.com/skozar/keepalive"
  version "0.4.0"
  url "https://github.com/skozar/keepalive/releases/download/keepalive-ui-v0.4.0/KeepaliveUI-0.4.0.zip"
  sha256 "907a13803e66bbb4e447e9109fc060f0fc903fb65c2efaf0ea56617c4f85984b"
  license "MIT"

  depends_on "keepalive"

  def install
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
