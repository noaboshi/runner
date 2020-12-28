import subprocess
import logging
import argparse
import tempfile
import os
import sys


def get_args():
    """
    parsing output from the cli and returning them
    """
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('command', help="the command to execute")  # mandatory
    parser.add_argument('-c', '--count', default=4, type=int,
                        help="number of times to execute the command")  # optional
    parser.add_argument('--failed-count', type=int,
                        help="number of allowed failed command invocation attempts before giving up, defaults to 'count' value")  # optional
    parser.add_argument('--sys-trace', action="store_true",
                        help="for each failed execution print logs for Disk IO, Memory, CPU usage and Network")  # optional
    parser.add_argument('--call-trace', action="store_true",
                        help="for each failed execution print all the system calls ran by the command")  # optional
    parser.add_argument('--log-trace', action="store_true",
                        help="for each failed execution print the command output logs")  # optional
    parser.add_argument('--net-trace', action="store_true",
                        help="for each failed execution create a 'pcap' file with the network traffic during the execution")  # optional
    parser.add_argument('--debug', action="store_true", help="debug mode")  # optional
    parser.add_argument('-h', '--help', action='store_true',
                        help='Show this help message and exit.')
    if "-h" in sys.argv or "--help" in sys.argv:
        parser.print_help(sys.stderr)
        sys.exit(1)
    args = parser.parse_args()
    return args


def logging_config(debug):
    """
    setting the level of logging messages sent to the console
    :param debug: if true will print logging message level debug and above,
                if false will print logging message level info and above
    """
    if debug:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO
    logging.basicConfig(format='%(levelname)s:%(message)s', level=log_level)


def build_command(command, strace_log):
    """
    building the command to execute, might add depending on the chosen flags
    :param command: the command given from cli
    :param strace_log: a file created to store strace output
    :return: the complete command to execute
    """
    if strace_log:
        logging.debug("adding strace output for the command")
        final_command = f"strace -o {strace_log.name} {command}"
    else:
        final_command = command
    return final_command


def print_sys_trace(disk_log, memory_log, cpu_log, network_log):
    """
    print to console each of the following log
    :param disk_log: Disk IO output
    :param memory_log: memory usage output
    :param cpu_log: CPU usage output
    :param network_log: tcpdump output
    """
    logging.debug("printing sys_trace logs")
    print("Failed to execute. printing resources logs:")
    print("Disk IO:")
    print(disk_log.stdout.read())
    print("Memory:")
    print(memory_log.stdout.read())
    print("CPU usage:")
    print(cpu_log.stdout.read())
    print("Network package counters:")
    print(network_log.stderr.read())


def print_system_calls(strace_log_path):
    """
    printing and closing the temp file
    :param strace_log_path: path of temp file
    """
    logging.debug("printing system call logs")
    print("Failed to execute. printing system calls:")
    file = open(strace_log_path, "r")
    print(file.read())
    file.close()


def print_log_trace(execute):
    """
    printing the stdout and stderr values for the command execute
    :param execute: the Popen object of the executed command
    """
    stdout = execute.stdout.read()
    stderr = execute.stderr.read()
    print("Failed to execute. printing available output logs:")
    if stdout:
        logging.debug("printing the command stdout")
        print("stdout:")
        print(stdout)
    if stderr:
        logging.debug("printing the command stderr")
        print("stderr:")
        print(stderr)


def main():
    args = get_args()
    executor(args.command, args.count, args.failed_count, args.sys_trace,
             args.call_trace, args.log_trace, args.net_trace, args.debug)


def executor(command, count=4, failed_count=None, sys_trace=False,
             call_trace=False, log_trace=False, net_trace=False, debug=False):
    """
    warps any command and outputs a summery of execution
    :param command: the command to execute
    :param count: number of times to execute the command
    :param failed_count: number of allowed failed command invocation attempts before giving up, defaults to 'count' value
    :param sys_trace: for each failed execution print logs for Disk IO, Memory, CPU usage and Network
    :param call_trace: for each failed execution print all the system calls ran by the command
    :param log_trace: for each failed execution print the command output logs
    :param net_trace: for each failed execution create a 'pcap' file with the network traffic during the execution
    :param debug: debug mode
    :return: the most frequent return code of the command
    """
    logging_config(debug)
    logging.debug("level of logging was configured")
    if call_trace:
        logging.debug("creating a temp file for strace output")
        strace_log = tempfile.NamedTemporaryFile()  # will create file only if needed
    else:
        strace_log = None
    command = build_command(command, strace_log)
    failed_count = failed_count or count  # if failed_count is none, use the value of count
    return_codes = {}  # the dict will be used as  return_code: number of appearances
    try:
        for run in range(1, count+1):
            if sys_trace or net_trace:
                logging.debug("creating tcpdump command")
                tcpdump_command = "tcpdump -v -i any"
                if net_trace:
                    logging.debug("creating pcap file")
                    tcpdump_command += f" -w traffic_on_num_{run}_execute.pcap"
                network_log = subprocess.Popen(tcpdump_command, shell=True, text=True,
                                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            logging.debug("now execute command for the %d time", run)
            execute = subprocess.Popen(command, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if sys_trace:
                logging.debug("running pidstat commands")
                disk_log = subprocess.Popen(f"pidstat -d -T ALL -p {execute.pid} 1", shell=True, text=True,
                                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                memory_log = subprocess.Popen(f"pidstat -r -T ALL -p {execute.pid} 1", shell=True, text=True,
                                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                cpu_log = subprocess.Popen(f"pidstat -u -T ALL -p {execute.pid} 1", shell=True, text=True,
                                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            execute.wait()
            if sys_trace or net_trace:
                network_log.terminate()
                network_log.wait()
                logging.debug("terminate the tcpdump command")
            if execute.returncode != 0:
                logging.debug('command return code is %d', execute.returncode)
                if failed_count == 0:  # if we reached the max failed attempts break out of the loop and exit.
                    logging.info('i reached max failed attempts, I GIVE UP')
                    break
                failed_count -= 1  # decrease the allowed fail until 0 than break
                if sys_trace:
                    print_sys_trace(disk_log, memory_log, cpu_log, network_log)
                if call_trace:
                    print_system_calls(strace_log.name)
                if log_trace:
                    print_log_trace(execute)
            elif net_trace and os.path.exists(f"traffic_on_num_{run}_execute.pcap"):
                logging.debug("execution succeeded, deleting the pcap file ")
                os.remove(f"traffic_on_num_{run}_execute.pcap")
            if execute.returncode in return_codes:  # check if return code happened before
                return_codes[execute.returncode] += 1  # if it was, will increase the key by 1
            else:
                return_codes[execute.returncode] = 1  # if it's the first time, will add to dict

    finally:
        if call_trace:
            logging.debug("close and delete the temp file for strace")
            strace_log.close()  # close the temp file so it will be deleted
        sorted_dict = sorted(return_codes.items(), reverse=True, key=lambda code: code[1])  # sort the dict by the values
        if sorted_dict:
            print(f"the most frequent return code was {sorted_dict[0][0]}")
            print("here is a summary of all return codes and how many times they happened:")
            for return_code, times in sorted_dict:
                print(f"the return code: {return_code}, happened {times} times")
            return sorted_dict[0][0]  # return the key with the biggest value
        else:
            logging.error("the command didn't run even once! something bad happened")


if __name__ == '__main__':
    main()
