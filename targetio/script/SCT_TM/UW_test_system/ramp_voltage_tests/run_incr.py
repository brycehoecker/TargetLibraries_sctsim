"""
Small homebrew module for reading and incrementing previousRun.txt on the
WIPAC server without relying on SSHFS. This is less confusing than pexpect
and uses paramiko to establish an SSH connection. It might be useful to
explore using paramiko to interact with the Pi on the backplane. I'd propose
using this for run incrementation over the SSHFS approach, but this text file
run numbering scheme is going to be gotten rid of soon in favor of a more
general SQL approach.
"""
import paramiko


def __connect_to_data_server() -> paramiko.SSHClient:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect("data.icecube.wisc.edu",
                username="bmode",
                key_filename="/Users/brent/.ssh/id_rsa")
    return ssh


def __get_current_run_number() -> str:
    ssh = __connect_to_data_server()
    ftp = ssh.open_sftp()
    file = ftp.file("/data/wipac/CTA/target5and7data/previousRun.txt", "r")
    run = file.readline()
    file.close()
    ftp.close()
    ssh.close()
    return run


def incr_run_number() -> int:
    prev_run = int(__get_current_run_number())
    new_run = prev_run + 1
    ssh = __connect_to_data_server()
    ftp = ssh.open_sftp()
    file = ftp.file("/data/wipac/CTA/target5and7data/previousRun.txt", "w")
    file.write(str(new_run))
    file.close()
    ftp.close()
    ssh.close()
    return new_run
