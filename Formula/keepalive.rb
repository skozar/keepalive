class Keepalive < Formula
  desc "Keep macOS awake for Teams during chosen hours"
  homepage "https://github.com/skozar/keepalive"
  version "0.1.0"
  url "https://github.com/skozar/keepalive/releases/download/v#{version}/keepalive"
  sha256 "b578155d4777e4cbf9e0b3344024de365a63e29e45983769a77ebd76636d966b"

  def install
    bin.install "keepalive"
  end

  def caveats
    <<~EOS
      To start the agent:
        keepalive start

      To run with custom schedule:
        keepalive start --schedule 04:00-12:00 --idle 180

      Logs: ~/Library/Logs/keepalive/keepalive.log

      IMPORTANT: Grant Accessibility permission to keepalive:
        System Settings → Privacy & Security → Accessibility
        Add: #{opt_bin}/keepalive
    EOS
  end
end
