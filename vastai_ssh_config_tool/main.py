import subprocess
import json
from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path
import click


SSH_CONFIG_PATH = Path("~/.ssh/config").expanduser().resolve()

SSH_CONFIG_FILE_BLOCK_START = "############### >>> THIS BLOCK IS USED FOR vastai-ssh-config-tool ################"
SSH_CONFIG_FILE_BLOCK_END =   "############### THIS BLOCK IS USED FOR vastai-ssh-config-tool <<< ################"


def get_instances() -> List[Dict[str, Any]]:
    cmd = "vastai show instances --raw"
    output = subprocess.check_output(cmd, shell=True).decode()
    output_parsed = json.loads(output)
    return output_parsed


def touch_missing() -> None:
    SSH_CONFIG_PATH.parent.mkdir(mode=0o700, exist_ok=True)
    SSH_CONFIG_PATH.touch(mode=0o600, exist_ok=True)


def create_empty_block():
    with open(SSH_CONFIG_PATH, "at") as file:
        file.write(f"\n{SSH_CONFIG_FILE_BLOCK_START}\n{SSH_CONFIG_FILE_BLOCK_END}\n")


def find_block_inside_ssh_config() -> Optional[Tuple[int, int]]:
    with open(SSH_CONFIG_PATH, "rt") as file:
        lines = file.readlines()
        lines = [line.strip() for line in lines]

        start_ixes = []
        end_ixes = []

        for line_ix, line in enumerate(lines):
            for pattern, ixes_array in zip(
                (SSH_CONFIG_FILE_BLOCK_START, SSH_CONFIG_FILE_BLOCK_END),
                (start_ixes, end_ixes),
            ):
                if pattern in line:
                    if line != pattern:
                        raise ValueError(
                            f"Tool-dedicated block in ssh config file ({SSH_CONFIG_PATH}) is corrupted (line {line_ix}). "
                            "Please fix it manually and re-run the tool."
                        )
                    ixes_array.append(line_ix)
        
        if len(start_ixes) > 0 or len(end_ixes) > 0:
            if not len(start_ixes) == len(end_ixes) == 1:
                raise ValueError(
                    f"Tool-dedicated block in ssh config file ({SSH_CONFIG_PATH}) is corrupted (lines {', '.join(start_ixes + end_ixes)}). "
                    "Please fix it manually and re-run the tool."
                )
            
            assert len(start_ixes) == len(end_ixes) == 1
            assert start_ixes[0] < end_ixes[0]
            return start_ixes[0], end_ixes[0] + 1


def replace_lines_inside_file(file_path: Path, start_line_ix: int, end_line_ix: int, new_lines: List[str]) -> None:
    with open(file_path, "rt") as file:
        lines = file.readlines()
    
    lines = lines[:start_line_ix] + [f"{line}\n" for line in new_lines] + lines[end_line_ix:]

    with open(file_path, "w") as file:
        file.write("".join(lines))


def generate_instances_ssh_config_lines(
    ssh_user: str,
    ssh_name_prefix: str,
    ssh_key_path: str,
) -> List[str]:
    lines = []

    lines += [
        f"Host {ssh_name_prefix}*",
        f"\tuser {ssh_user}",
        f"\tidentityfile {ssh_key_path}",
    ]

    instances = get_instances()
    for instance in instances:
        instance_id = instance['id']
        host_name = f"{ssh_name_prefix}{instance_id}"

        if instance["actual_status"] != "running":
            print(f"Instance {instance_id} is not running, it will not be added into ssh config file.")
            continue

        ssh_ports = {rec["HostPort"] for rec in instance["ports"].get("22/tcp", [])}
        if len(ssh_ports) != 1:
            print(f"Failed to detect ssh port for instance {instance_id}. This instance will be skipped.")

        lines += [
            "",
            f"Host {host_name}",
            f"\thostname {instance['public_ipaddr']}",
            f"\tport {ssh_ports.pop()}",
        ]

        print(f"Found instance {instance_id}: use `ssh {host_name}` to connect")
    
    return lines


@click.command()
@click.option(
    "--ssh-user",
    default="root",
)
@click.option(
    "--ssh-host-name-prefix",
    default="vast",
)
@click.option(
    "--ssh-key-path",
    default="~/.ssh/vast_key",
)
def configure(ssh_user: str, ssh_host_name_prefix: str, ssh_key_path: str):
    touch_missing()

    block_ixes = find_block_inside_ssh_config()
    if block_ixes is None:
        create_empty_block()
        block_ixes = find_block_inside_ssh_config()
    if block_ixes is None:
        raise RuntimeError(f"Failed to create a tool-dedicated block inside ssh config file ({SSH_CONFIG_PATH})")
    
    instances_ssh_config = generate_instances_ssh_config_lines(
        ssh_user=ssh_user,
        ssh_name_prefix=ssh_host_name_prefix,
        ssh_key_path=ssh_key_path,
    )
    
    replace_lines_inside_file(
        file_path=SSH_CONFIG_PATH,
        start_line_ix=block_ixes[0] + 1,
        end_line_ix=block_ixes[1] - 1,
        new_lines=instances_ssh_config,
    )


if __name__ == "__main__":
    configure()
