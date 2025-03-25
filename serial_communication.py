import serial
import argparse
import sys
import time
import logging
from typing import Any, Optional, Dict
from serial.tools import list_ports
import os

# Add the project root to sys.path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from imports.serial_commander.utils.command_parser import parse_response
from imports.serial_commander.config.config_loader import load_esp32config

default_config = load_esp32config().get('ESP32_UART_CONFIG')

class SerialCommunication:
    def __init__(self, config: Optional[Dict] = default_config, logger: Optional[logging.Logger] = None,
                 max_retries: int = 3, retry_delay: float = 0.5):
        """Initialize serial communication with retry parameters.

        Args:
            logger: Optional logger instance
            max_retries: Maximum number of command retries (default: 3)
            retry_delay: Delay between retries in seconds (default: 0.5)
        """
        self.serial_port = None
        self.last_response = None
        self.logger = logger or logging.getLogger(__name__)
        self.uart_config = config
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def open_serial(self, port: str = None) -> None:
        """
        Open serial connection if not already open.

        Args:
            port: Optional port name (default: None)
        """
        if port is None:
            port = self.uart_config['DEFAULT_PORT']

        if self.serial_port is None or not self.serial_port.is_open:
            # Create serial port with DTR disabled
            self.serial_port = serial.Serial(
                port=port,
                baudrate=self.uart_config['BAUD_RATE'],
                timeout=self.uart_config['TIMEOUT'],
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                rtscts=False,
                dsrdtr=False  # Disable hardware flow control
            )

            # Important: Set DTR and RTS before opening
            self.serial_port.dtr = False
            self.serial_port.rts = False

            # Wait for ESP32 to stabilize
            time.sleep(self.uart_config['ESP32_BOOT_DELAY'])  # Give ESP32 time to complete its boot sequence

            # Clear buffers
            self.serial_port.reset_input_buffer()
            self.serial_port.reset_output_buffer()

            # Read any pending data
            while self.serial_port.in_waiting:
                self.serial_port.read_all()
                time.sleep(0.1)

    def close_serial(self) -> None:
        """Close serial connection if open."""
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
            self.logger.debug("Serial port closed")

    def send_command(self, command: str, retry_count: int = 0,
                    context: Optional[Any] = None) -> bool:
        """Send command over serial and handle response with retry mechanism.

        Args:
            command: Command to send
            retry_count: Current retry attempt (used internally)
            context: Optional context for logging

        Returns:
            bool: True if command was successful, False otherwise
        """
        try:
            self._ensure_connection()
            self._clear_pending_data()

            # Log the command and retry attempt if applicable
            if retry_count > 0:
                self.logger.debug(f"Retry attempt {retry_count}/{self.max_retries} for command: {command}")
            else:
                self.logger.debug(f"Sending command: [{command}]")

            self._send_command(command)

            # Read response with timeout
            response = self._read_response()

            if not response:
                self.logger.warning(f"No response received for command: {command}")
                return self._handle_retry(command, retry_count)

            if context is not None and hasattr(context, 'log_response'):
                lines = response.split('\n')
                for line in lines:
                    context.log_response(line)

            self.last_response = response

            # Parse response and handle retry if needed
            parse_result = self._parse_response(response)
            if not parse_result and retry_count < self.max_retries:
                return self._handle_retry(command, retry_count)

            return parse_result

        except serial.SerialException as e:
            self._handle_serial_exception(e)
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error in serial communication: {str(e)}")
            return False

    def _send_command(self, command: str) -> None:
        """
        Send the command and wait for a response.

        Args:
            command: Command to send
        """
        command_bytes = (command + self.uart_config['LINE_TERMINATOR']).encode('utf-8')
        self.serial_port.write(command_bytes)
        self.serial_port.flush()
        time.sleep(0.1)

    def _read_response(self) -> str:
        """
        Read the response from the serial port.

        Returns:
            str: Response from the serial port
        """
        response = ""
        start_time = time.time()

        while time.time() - start_time < self.uart_config['TIMEOUT']:
            if self.serial_port.in_waiting:
                try:
                    new_data = self.serial_port.read_all().decode('utf-8', errors='ignore')
                    response += new_data

                    # Check if we have a complete response
                    if "RESPONSE:" in response and self.uart_config['LINE_TERMINATOR'] in response:
                        break
                except UnicodeDecodeError:
                    # If we get invalid UTF-8, clear the buffer and continue
                    self.serial_port.reset_input_buffer()
                    self.logger.warning("Received invalid UTF-8 data, clearing buffer")
                    continue

            time.sleep(0.05)  # Small delay to prevent busy waiting

        return response

    def _ensure_connection(self) -> None:
        """Ensure the serial connection is open."""
        if not self.serial_port or not self.serial_port.is_open:
            self.open_serial()

    def _clear_pending_data(self) -> None:
        """Clear any pending data in the serial buffer."""
        self.serial_port.reset_input_buffer()

    def _handle_serial_exception(self, e: Exception) -> None:
        """
        Handle serial exceptions and attempt to reopen the connection.

        Args:
            e: Exception to handle
        """
        self.logger.error(f"Serial communication error: {str(e)}")
        try:
            self.close_serial()
            self.open_serial()
        except Exception as e:
            self.logger.error(f"Failed to reopen serial connection: {str(e)}")

    def _handle_retry(self, command: str, retry_count: int, context: Optional[Any] = None) -> bool:
        """Handle command retry logic.

        Args:
            command: Original command
            context: Command context
            retry_count: Current retry count

        Returns:
            bool: Result of retry attempt or False if max retries reached
        """
        if retry_count < self.max_retries:
            self.logger.warning(f"Command failed, attempting retry {retry_count + 1}/{self.max_retries}")
            time.sleep(self.retry_delay)  # Wait before retry
            return self.send_command(command, retry_count + 1, context)
        else:
            self.logger.error(f"Command failed after {self.max_retries} retries")
            return False

    def _parse_response(self, response) -> bool:
        """Parse and verify response using the parser.

        Args:
            response: Response string to parse

        Returns:
            bool: True if parsing was successful and status is OK, False otherwise
        """
        parsed = parse_response(response, self.logger)

        if parsed:
            self.logger.debug(f"Parsed response: {parsed}")
            if parsed['status'] == 'OK':
                self.logger.debug("Response status is OK.")
                return True
            else:
                self.logger.warning(f"Response status is not OK: {parsed['status']}")
        else:
            self.logger.error("Failed to parse response. No valid data returned.")

        return False

    def __enter__(self):
        """Context manager entry."""
        self.open_serial()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close_serial()

    def list_available_ports(self) -> list:
        """List all available serial ports.

        Returns:
            list: A list of available COM ports.
        """
        ports = list_ports.comports()
        available_ports = [port.device for port in ports]
        self.logger.info(f"Available COM ports: {available_ports}")
        return available_ports

def setup_logging(level: int = logging.INFO) -> None:
    """
    Configure logging with a standard format.

    Args:
        level: Logging level (default: logging.INFO)
    """
    logging.basicConfig(
        level=level,
        format='%(asctime)s.%(msecs)03d [%(levelname)s] %(message)s',
        datefmt='%H:%M:%S'
    )