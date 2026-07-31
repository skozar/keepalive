class KeepaliveCli < Formula
  desc "Keep macOS awake for Teams during chosen hours"
  homepage "https://github.com/skozar/keepalive"
  version "0.11.9"
  url "https://github.com/skozar/keepalive/releases/download/v#{version}/keepalive-cli-#{version}.tar.gz"
  sha256 "41dd7db3c689d1a8b6e5f495b6a4108803ac45cc85e49f5dc7bd74c93db2421a"

  def install
    # Tarball contains Contents/ from a PyInstaller --windowed .app bundle
    # plus codesign.sh at the root.
    # Homebrew unpacks into staging. Reconstruct the .app in libexec
    # so macOS identifies the process as "keepalive-cli" in Accessibility.
    app = libexec/"keepalive-cli.app"
    (app/"Contents").mkpath
    FileUtils.mv(Dir["Contents/*"], app/"Contents")

    # Install codesign.sh for `keepalive-cli setup` use
    (prefix/"scripts").mkpath
    FileUtils.cp("codesign.sh", prefix/"scripts/codesign.sh")
    chmod 0755, prefix/"scripts/codesign.sh"

    # Ad-hoc sign initially (proper signing happens via `keepalive-cli setup`)
    system "codesign", "--force", "--deep", "--sign", "-", app.to_s

    # CLI symlink through .app
    bin.install_symlink app/"Contents/MacOS/keepalive-cli" => "keepalive-cli"
  end

  def caveats
    <<~EOS
      Run setup once to create a code signing certificate (needed for
      accessibility permissions to persist across brew upgrades):

        keepalive-cli setup

      To start the agent:
        keepalive-cli start

      Logs: ~/Library/Logs/keepalive/keepalive.log
    EOS
  end
end