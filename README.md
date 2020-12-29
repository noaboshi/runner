# RUNNER

Python home task.
Warps any command and outputs a summery of execution, with the following optional flags: 
  - -c --count N - Number of times to run the given command 
  - --failed-count N - Number of allowed failed command invocation attempts before giving up 
  - --sys-trace - For each failed execution, create a log for each of the following values, measured during command execution:
    -  Disk IO 
    -  Memory 
    -  Processes/threads and cpu usage of the command 
    -  Network card package counters
  - --call-trace - For each failed execution, add also a log with all the system calls ran by the command
  - --log-trace - For each failed execution, add also the command output logs (stdout, stderr) 
  - --net-trace - For each failed execution, create a ‘pcap’ file with the network traffic during the execution.
  - --debug - Debug mode, show each instruction executed by the script 
  - -h --help - Print a usage message to STDERR explaining how the script should be used.


  **For the flags: --sys-trace and --net-trace to work the script must be run with root privileges**


## Usage
Running "echo hello" 3 times: 
```
$ python3.7 runner.py "echo hello" -c 3 
the most frequent return code was 0
here is a summary of all return codes and how many times they happened:
the return code: 0, happened 3 times
```

Try to run "rm non_exist_file" 3 times, max failed attempts set to 2, will print the output logs: 
```
$ python3.7 runner.py "rm non_exist_file" -c 3 --failed-count 2 --log-trace
Failed to execute. printing available output logs:
stderr:
rm: non_exist_file: No such file or directory
Failed to execute. printing available output logs:
stderr:
rm: non_exist_file: No such file or directory
INFO:I reached max failed attempts, I GIVE UP
The most frequent return code was 1
Here is a summary of all return codes and how many times they happened:
The return code: 1, happened 2 times
```


## Requirements 
- Python 3.7 +
- Non Python Requirements 
    - strace
    - sysstat
    - tcpdump

## References
- https://docs.python.org/3/
- https://stackabuse.com/executing-shell-commands-with-python/
- https://stackoverflow.com/a/613218
- https://stackoverflow.com/a/95246
- https://www.tutorialspoint.com/generate-temporary-files-and-directories-using-python
- https://stackoverflow.com/questions/7989922/opening-a-process-with-popen-and-getting-the-pid
- https://www.saltycrane.com/blog/2008/09/how-get-stdout-and-stderr-using-python-subprocess-module/
- https://code-maven.com/python-capture-stdout-stderr-exit
- https://github.com/sysstat/sysstat
- https://stackoverflow.com/a/40160354
- https://stackoverflow.com/a/46307456
- https://stackoverflow.com/a/35848313
- https://stackoverflow.com/a/4042861
- https://dillinger.io

## Challenges 
During my work on this assignment I encountered many new subjects to explore,
Here I present a few subjects which were the most challenging for me:
**-- Sys-trace Flag** - I researched a lot trying to find the right monitor tool to be used for     this flag, and the right way to present it's conclusions.
    the tool needed to run continuously until the executed command finished and provide all values required.
    Sysstat commands has answered most of my needs and was convenient to work with therefore it was my final choice
    
**--Writing Tests** - working on this task was my first encounter in writing tests for my code, I have invested time to read and research what tests should I run, how to work with pytest and how can I capture the output of my script in order to check it.
A realization I made only by the end of my writing is I shouldn't have kept the work on writing tests for last. 
If I started to write tests at the same time I wrote the script, I would have noticed errors more easily and I could write my code in a more convenient way to test. 

**--Spliting the code** - At first I planned for each flag to have it's own function, but as I proceed I had more and more trouble with separating the flags functionality from the main command. Many of my variables depended on one another and it made the main function a bit messy and complicated.
Finally I tried to separate at least some of the functionality to a smaller functions in order to leave only the necessary code on the main.  




