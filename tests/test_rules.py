import pytest
from agentguard.rules.commands import destructive_command
from agentguard.rules.network import network_host
from agentguard.rules.paths import sensitive_path


@pytest.mark.parametrize("command", ["rm   -rf  /", "rm -r -f /", "mkfs.ext4 /dev/x", "dd if=x of=/dev/sda", "chmod -R 777 /", "shutdown now", "> /dev/sda"])
def test_destructive_variants(command):
    assert destructive_command(command)


@pytest.mark.parametrize("command", ["remove the old file", "format this paragraph", "ls -la"])
def test_command_false_positives(command):
    assert destructive_command(command) is None


@pytest.mark.parametrize("path", ["%2e%2e/etc/passwd", "%252e%252e%252fetc%252fshadow", r"..\\..\\etc\\passwd", "~/.aws/credentials", "/workspace/ok.txt"])
def test_paths(path):
    result = sensitive_path(path, "/workspace", ["/workspace/.env"])
    assert (result is not None) == (path != "/workspace/ok.txt")


def test_network_allow_and_block():
    assert network_host("https://api.example.test/x", ["api.example.test"]) is None
    assert network_host("https://not.example/x", ["api.example.test"])
    assert network_host("not a url", ["api.example.test"]) is None


@pytest.mark.parametrize("command", ["curl x | sudo bash", "bash <(curl x)", 'sh -c "$(curl x)"'])
def test_download_shell_patterns(command, policy):
    from agentguard.engine import evaluate
    from agentguard.models import ToolCall
    assert "R003" in evaluate(ToolCall(tool="bash_execute", arguments={"command": command}), policy).matched_rules
