#!/usr/bin/env python
import sys
import logging
import argparse
import os

# Add the project root to sys.path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from imports.serial_commander.serial_communication import SerialCommunication
from imports.serial_commander.config.config_loader import load_esp32config

def setup_logging(level: int = logging.INFO) -> None:
    """Configure logging with a standard format."""
    logging.basicConfig(
        level=level,
        format='%(asctime)s.%(msecs)03d [%(levelname)s] %(message)s',
        datefmt='%H:%M:%S'
    )

def main() -> None:
    """Command-line interface for serial communication."""
    config = load_esp32config().get('ESP32_UART_CONFIG')

    parser = argparse.ArgumentParser(
        description="Send text messages over serial port and receive responses"
    )
    parser.add_argument(
        "message",
        help="Text message to send"
    )
    parser.add_argument(
        "-p", "--port",
        default=config.get('DEFAULT_PORT'),
        help=f"Serial port (default: {config.get('DEFAULT_PORT')})"
    )
    parser.add_argument(
        "-b", "--baudrate",
        type=int,
        default=config.get('BAUD_RATE'),
        help=f"Baud rate (default: {config.get('BAUD_RATE')})"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(level=logging.DEBUG if args.verbose else logging.INFO)
    logger = logging.getLogger(__name__)

    # Create sender instance
    sender = SerialCommunication(
        config=config,
        logger=logger,
        max_retries=0,
    )

    # Send message and get response
    success = sender.send_command(args.message)

    # Handle result
    if success:
        logger.info(f"SUCCESS: Command sent to {args.port}: [{args.message}]")
        logger.info(f"RESPONSE: [{sender.last_response}]")
        sys.exit(0)
    else:
        logger.error(f"ERROR: Command failed to send to {args.port}: '{args.message}'")
        sys.exit(1)

if __name__ == "__main__":
    main()