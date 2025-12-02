# Flex Provisioner

A Python tool for creating Fortinet FortiFlex VM entitlements. 
## Overview

Flex Provisioner will deploy new FortiFlex assets based on the configuration.yaml file.
Use this to just-in-time generate new Flex vm-license codes

## Prerequisites

- Python 3.x
- Active Fortinet FortiFlex account
- FortiFlex API credentials (username and token)
- FortiFlex program with configured entitlements

## Installation

1. Clone the repository:
```bash
git clone https://github.com/michaelbellgh/flex_provisioner.git
cd flex_provisioner
```

2. Install required dependencies:
```bash
pip install requests pyyaml pyperclip
```

## Configuration

### 1. Create `credentials.py`

Create a file named `credentials.py` in the project root with your API credentials:

```python
api_username = "your_fortinet_username"
api_token = "your_api_token"
```

**Important**: Add `credentials.py` to your `.gitignore` to avoid committing sensitive credentials.

### 2. Create `config.yaml`

Create a `config.yaml` file with your FortiFlex configuration:

```yaml
general:
  flex_serial: "YOUR_PROGRAM_SERIAL_NUMBER"

fortigate:
  configuration: "YOUR_CONFIGURATION_NAME"
```

- `flex_serial`: Your FortiFlex program serial number
- `configuration`: The name of your FortiGate configuration in FortiFlex

## Usage

Run the provisioner with the desired configuration:

```bash
python flex_provisioner.py fortigate
```

### Entitlement States

The tool handles different entitlement states:

- **STOPPED**: Reactivates the entitlement and generates a new token
- **PENDING**: Regenerates the token for the existing entitlement
- **None available**: Creates a brand new entitlement

## Configuration Options

### Clipboard Support

Clipboard integration is enabled by default. To disable:

```python
CLIPBOARD_SUPPORT = False
```

### Custom Entitlements

When creating new entitlements, you can customize the description by modifying the `create_fortiflex_entitlement()` call in `main()`.
