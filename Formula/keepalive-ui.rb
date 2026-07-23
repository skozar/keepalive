class KeepaliveUi < Formula
  desc "Menu bar controller for the keepalive activity agent"
  homepage "https://github.com/skozar/keepalive"
  version "0.5.0"
  url "https://github.com/skozar/keepalive/releases/download/v0.5.0/KeepaliveUI-0.5.0.zip"
  sha256 "bf140fbeccfdde74885f4dd198ddd4a944f4c660d630fe0a9fc5f01465980d31"
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
