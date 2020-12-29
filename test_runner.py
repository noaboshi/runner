import runner
import io
import os
from unittest.mock import patch


@patch("sys.stdout", new_callable=io.StringIO)
def test_count_and_log_trace_flags(mock_stdout: io.StringIO):
    runner.executor("echo hello && false", count=5, log_trace=True)
    output_of_runner = mock_stdout.getvalue()
    assert output_of_runner.count("hello") == 5


@patch("sys.stdout", new_callable=io.StringIO)
def test_log_trace_false_will_not_print_output(mock_stdout: io.StringIO):
    runner.executor("echo hello && false", count=5, log_trace=False)
    output_of_runner = mock_stdout.getvalue()
    assert output_of_runner.count("hello") == 0


@patch("sys.stdout", new_callable=io.StringIO)
def test_failed_count_flag_will_stop_at_2(mock_stdout: io.StringIO):
    runner.executor("echo hello && false", count=5, failed_count=2, log_trace=True)
    output_of_runner = mock_stdout.getvalue()
    assert output_of_runner.count("hello") == 2


@patch("sys.stdout", new_callable=io.StringIO)
def test_sys_trace_flag_expected_output(mock_stdout: io.StringIO):
    runner.executor("echo hello && false", count=1, sys_trace=False)
    output_of_runner = mock_stdout.getvalue()
    assert "kB_rd/s" not in output_of_runner  # Disk IO output
    assert "%MEM" not in output_of_runner  # memory usage output
    assert "%CPU" not in output_of_runner  # CPU usage output
    assert "packets captured" not in output_of_runner  # tcpdump output
    runner.executor("echo hello && false", count=1, sys_trace=True)
    output_of_runner = mock_stdout.getvalue()
    assert "kB_rd/s" in output_of_runner  # Disk IO output
    assert "%MEM" in output_of_runner  # memory usage output
    assert "%CPU" in output_of_runner  # CPU usage output
    assert "packets captured" in output_of_runner  # tcpdump output


@patch("sys.stdout", new_callable=io.StringIO)
def test_call_trace_flag_expected_output(mock_stdout: io.StringIO):
    runner.executor("echo hello && false", count=1, call_trace=False)
    output_of_runner = mock_stdout.getvalue()
    assert 'execve("/usr/bin/echo", ["echo", "hello"]' not in output_of_runner  # first system call for this command
    runner.executor("echo hello && false", count=1, call_trace=True)
    output_of_runner = mock_stdout.getvalue()
    assert 'execve("/usr/bin/echo", ["echo", "hello"]' in output_of_runner  # first system call for this command


def test_net_trace_flag_created_file():
    runner.executor("echo hello && false", count=1, net_trace=False)
    pcap_file = "traffic_on_num_1_execute.pcap"
    assert not os.path.exists(pcap_file)
    runner.executor("echo hello && false", count=1, net_trace=True)
    assert os.path.exists(pcap_file)
    os.remove(pcap_file)


def test_expected_final_return_code():
    success_code = runner.executor("echo hello", count=3)
    assert success_code == 0
    failure_code = runner.executor("echo hello && false", count=3)
    assert failure_code == 1
