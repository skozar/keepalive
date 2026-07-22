class KeepaliveUi < Formula
  desc "Menu bar controller for the keepalive activity agent"
  homepage "https://github.com/skozar/keepalive"
  url "https://github.com/skozar/keepalive/releases/download/keepalive-ui-v0.1.0/Keepalive-0.1.0.zip"
  sha256 "e2502d6e46367ff6d45c08fb18fb325efd867afa88bdfd914b96dc3f6ab5027f"
  license "MIT"

  depends_on "keepalive"

  def install
    system "ls", "-laR"
    app = Dir.glob("**/*.app").first
    if app
      prefix.install app
    else
      odie "No .app bundle found in #{Dir.pwd}"
    end
  end

  def post_install
    target = "/Applications/Keepalive.app"
    if File.exist?(target) || File.symlink?(target)
      opoo "#{target} already exists. Removing to create symlink."
      FileUtils.rm_rf(target)
    end
    system "ln", "-sf", prefix/"Keepalive.app", target
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
