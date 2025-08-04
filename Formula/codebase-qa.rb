class CodebaseQa < Formula
  desc "RAG-powered codebase question answering tool with Streamlit UI"
  homepage "https://github.com/codebase-qa/codebase-qa"
  url "https://github.com/codebase-qa/codebase-qa/archive/v0.1.0.tar.gz"
  sha256 "PLACEHOLDER_SHA256"  # This will be updated when the release is created
  license "MIT"
  head "https://github.com/codebase-qa/codebase-qa.git", branch: "main"

  depends_on "python@3.11"

  def install
    # Install Python dependencies
    system "python3", "-m", "pip", "install", "--prefix=#{libexec}", "."
    
    # Create the bin directory and symlink the executable
    bin.install Dir["#{libexec}/bin/*"]
    bin.env_script_all_files(libexec/"bin", PYTHONPATH: ENV["PYTHONPATH"])
    
    # Create a wrapper script for the CLI
    (bin/"codebase-qa").write <<~EOS
      #!/bin/bash
      exec "#{libexec}/bin/codebase-qa" "$@"
    EOS
    chmod 0755, bin/"codebase-qa"
  end

  test do
    # Test that the CLI is available
    system "#{bin}/codebase-qa", "--help"
    
    # Test version command
    assert_match "codebase-qa version 0.1.0", shell_output("#{bin}/codebase-qa version")
  end
end 