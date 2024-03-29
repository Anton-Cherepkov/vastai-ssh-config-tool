## Description
This tool automatically configures your `.ssh/config` file in accordance with your current vast.ai instances. The main goal of this tool is to save your time if you operate with many instances.

## How to use
1. Run `pip install git+https://github.com/Anton-Cherepkov/vastai-ssh-config-tool.git`
2. Go to https://vast.ai/console/cli/. Copy the command under the heading "Login / Set API Key" and run it. The command will be something like `vastai set api-key xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`.
3. Run `vastai-ssh-config`.

## Usage
```
Usage: vastai-ssh-config [OPTIONS]

Options:
  --ssh-user TEXT
  --ssh-host-name-prefix TEXT
  --ssh-key-path TEXT
  --help                       Show this message and exit.
```
