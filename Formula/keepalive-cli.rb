class KeepaliveCli < Formula
  desc "Keep macOS awake for Teams during chosen hours"
  homepage "https://github.com/skozar/keepalive"
  version "0.11.9"
  url "https://github.com/skozar/keepalive/releases/download/v#{version}/keepalive-cli-#{version}.tar.gz"
  sha256 "3b24efa322a8aa9eaaf6ac4761d8c3ba6974c78453b4d21adeede5fca53051ce"

  def install
    # Tarball contains Contents/ from a PyInstaller --windowed .app bundle.
    # Homebrew unpacks and CDs into Contents/. Reconstruct the .app in libexec
    # so macOS identifies the process as "keepalive-cli" in Accessibility.
    app = libexec/"keepalive-cli.app"
    (app/"Contents").mkpath
    FileUtils.mv(Dir["Contents/*"], app/"Contents")

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