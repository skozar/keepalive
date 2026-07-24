class KeepaliveCli < Formula
  desc "Keep macOS awake for Teams during chosen hours"
  homepage "https://github.com/skozar/keepalive"
  version "0.7.0"
  url "https://github.com/skozar/keepalive/releases/download/v#{version}/keepalive-cli-#{version}.tar.gz"
  sha256 "82393b9495d43361e98dbdf7fdad235b8354896e32ba583921ce690fe7d1fe38"

  def install
    libexec.install Dir["*"]
    bin.install_symlink libexec/"keepalive-cli"
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
