import logging
import re
from typing import Optional
from config.config_loader import load_esp32config

def parse_response(response, logger: Optional[logging.Logger] = None):
    """Parse the response from ESP32.

    Args:
        response: Response string to parse
        logger: Optional logger instance

    Returns:
        dict: Parsed response data or None if parsing fails
    """
    logger = logger or logging.getLogger(__name__)

    if not isinstance(response, str):
        logger.error(f"Invalid response type: {type(response)}. Expected string.")
        return None

    if not response:
        logger.error("No response provided for parsing.")
        return None

    # Split response into lines and look for the actual response line
    lines = response.split('\n')
    valid_responses = []

    for line in lines:
        line = line.strip()

        # Only process lines that start with "RESPONSE: "
        if line.startswith("RESPONSE: "):
            valid_responses.append(line)  # Collect valid response lines
        else:
            logger.debug(f"Ignoring line: {line}")  # Log ignored lines

    # Add validation for no valid responses found
    if not valid_responses:
        logger.warning("No valid response lines found in the input")
        return None

    # Process collected valid response lines
    for line in valid_responses:

        logger.debug(f"Parsing valid response: {line}")  # Log the response being parsed

        for response_type, pattern in load_esp32config().get('ESP32_RESPONSE_PATTERNS').items():
            match = re.match(pattern, line)
            if match:
                groups = match.groups()
                logger.debug(f"Matched response type: {response_type} with groups: {groups}")  # Log matched response

                # Handle different response types
                if response_type == 'GPIO_OUTPUT':
                    pin, status = groups
                    return {
                        'type': 'GPIO_OUTPUT',
                        'pin': int(pin),
                        'status': status
                    }

                elif response_type == 'GPIO_INPUT':
                    pin, value, status = groups
                    return {
                        'type': 'GPIO_INPUT',
                        'pin': int(pin),
                        'value': value,
                        'status': status
                    }

                elif response_type == 'PWM_OUTPUT':
                    pin, status = groups
                    return {
                        'type': 'PWM_OUTPUT',
                        'pin': int(pin),
                        'status': status
                    }

                elif response_type == 'DAC_OUTPUT':
                    pin, status = groups
                    return {
                        'type': 'DAC_OUTPUT',
                        'pin': int(pin),
                        'status': status
                    }

                elif response_type == 'ADC_INPUT':
                    pin, value, status = groups
                    return {
                        'type': 'ADC_INPUT',
                        'pin': int(pin),
                        'value': int(value),
                        'status': status
                    }

                elif response_type == 'GEN_SIGNAL':
                    sig_type, value, status = groups
                    return {
                        'type': 'GEN_SIGNAL',
                        'signal_type': int(sig_type),
                        'value': float(value),
                        'status': status
                    }

                elif response_type == 'CLOSED_LOOP':
                    id_val, status = groups
                    return {
                        'type': 'CLOSED_LOOP',
                        'id': int(id_val),
                        'status': status
                    }

    logger.error("No valid response matched.")
    return None