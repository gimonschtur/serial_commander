# Serial Commander

A Python library for reliable serial communication with ESP32 devices, featuring robust error handling, automatic retries, and structured response parsing.

## Features

- Reliable serial communication with configurable retry mechanisms
- Structured response parsing for various ESP32 commands
- Context manager support for safe resource handling
- Comprehensive logging system
- Command-line interface for quick testing
- Configuration management via JSON files

## Components

### 1. Serial Communication (`serial_communication.py`)
The core module handling serial port communication with the following features:
- Automatic connection management
- Command retry mechanism
- Response parsing
- Error handling
- Context manager support (`with` statement)

### 2. Command Parser (`utils/command_parser.py`)
Handles parsing of ESP32 responses for different command types:
- GPIO Input/Output
- PWM Output
- DAC Output
- ADC Input
- Signal Generation
- Closed Loop Control

### 3. Configuration Management (`config/config_loader.py`)
Manages configuration loading and validation:
- JSON-based configuration
- Validation of required fields
- ESP32-specific settings

## Configuration

The system uses a JSON configuration file (`config/esp32_config.json`) with the following structure:
```json
{
    "ESP32_UART_CONFIG": {
        "DEFAULT_PORT": "COM127",
        "BAUD_RATE": 115200,
        "TIMEOUT": 2.0,
        "LINE_TERMINATOR": "\r\n",
        "ESP32_BOOT_DELAY": 2.0
    },
    "ESP32_RESPONSE_PATTERNS": {
        "GPIO_OUTPUT": "...",
        "GPIO_INPUT": "...",
        "PWM_OUTPUT": "...",
        "DAC_OUTPUT": "...",
        "ADC_INPUT": "...",
        "GEN_SIGNAL": "...",
        "CLOSED_LOOP": "..."
    }
}
```

## Usage

### Command Line Interface
```bash
python serial_communication.py "your_command" [-p PORT] [-b BAUDRATE] [-v]
```

Options:
- `-p, --port`: Serial port (default from config)
- `-b, --baudrate`: Baud rate (default from config)
- `-v, --verbose`: Enable verbose logging

### Python API
```python
from serial_communication import SerialCommunication
from config.config_loader import load_esp32config

# Load configuration
config = load_esp32config().get('ESP32_UART_CONFIG')

# Create communication instance
with SerialCommunication(config=config) as comm:
    success = comm.send_command("your_command")
    if success:
        print(f"Response: {comm.last_response}")
```

## Error Handling

The library implements comprehensive error handling:
- Serial port connection issues
- Invalid responses
- Unicode decode errors
- Configuration errors
- Command timeouts

## Requirements

- Python 3.6+
- pyserial

## License

This project is licensed under the GNU General Public License.