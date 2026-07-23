class Keepalive < Formula
  desc "Keep macOS awake for Teams during chosen hours"
  homepage "https://github.com/skozar/keepalive"
  version "0.5.3"
  url "https://github.com/skozar/keepalive/releases/download/v#{version}/keepalive-#{version}.tar.gz"
  sha256 "20eebb01717a2e150ee9c08b136339aef9a6c33d8b6ec422a795309d0cd7a84a"

  def install
    libexec.install Dir["*"]
    bin.install_symlink libexec/"keepalive"
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
