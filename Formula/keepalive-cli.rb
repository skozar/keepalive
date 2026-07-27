class KeepaliveCli < Formula
  desc "Keep macOS awake for Teams during chosen hours"
  homepage "https://github.com/skozar/keepalive"
  version "0.11.2"
  url "https://github.com/skozar/keepalive/releases/download/v#{version}/keepalive-cli-#{version}.tar.gz"
  sha256 "f6f2b59e87d85d73c4609dbd2f2321354ac5494f415b618f77c54cc3eb88e370"

  def install
    libexec.install Dir["*"]
    bin.install_symlink libexec/"keepalive-cli" => "keepalive-cli"
    # Ad-hoc code-sign so the binary appears in Accessibility preferences.
    system "codesign", "--force", "--deep", "--sign", "-", "#{libexec}/keepalive-cli"
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
