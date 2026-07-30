class KeepaliveCli < Formula
  desc "Keep macOS awake for Teams during chosen hours"
  homepage "https://github.com/skozar/keepalive"
  version "0.11.6"
  url "https://github.com/skozar/keepalive/releases/download/v#{version}/keepalive-cli-#{version}.tar.gz"
  sha256 "d0d9224b3dbd7a390d683c2301fded1a3c5d6c8455d876963e372cd6700b69b4"

  def install
    # Tarball contains Contents/ from a PyInstaller --windowed .app bundle.
    # Homebrew unpacks and CDs into Contents/. Reconstruct the .app in libexec
    # so macOS identifies the process as "keepalive-cli" in Accessibility.
    app = libexec/"keepalive-cli.app"
    (app/"Contents").mkpath
    FileUtils.mv(Dir["*"], app/"Contents")

    # Ad-hoc code-sign the .app bundle
    system "codesign", "--force", "--deep", "--sign", "-", app.to_s

    # CLI symlink through .app
    bin.install_symlink app/"Contents/MacOS/keepalive-cli" => "keepalive-cli"
  end

  def caveats
    <<~EOS
      To start the agent:
        keepalive-cli start

      To run with custom schedule:
        keepalive-cli start --schedule 08:00-17:00 --idle 180

      Logs: ~/Library/Logs/keepalive/keepalive.log

      IMPORTANT: Grant Accessibility permission to keepalive-cli:
        System Settings → Privacy & Security → Accessibility
        Add: #{opt_bin}/keepalive-cli
    EOS
  end
end