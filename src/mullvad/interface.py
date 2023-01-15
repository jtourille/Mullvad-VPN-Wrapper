import io
import random
import re
import subprocess
from collections import defaultdict
from typing import Dict, Union

regex_country = re.compile(r"^.*\s\(([a-z]{2})\)$")
regex_city = re.compile(r"^\t.*\s\(([a-z]{3})\)")
regex_server = re.compile(r"^\t\t([^\(]*)\s\(")

regex_status = re.compile(r"^(Disconnected|Connected)")
regex_status_server = re.compile(r"^Connected to (\S*)\s")

regex_set_server = re.compile(r"^Relay constraints updated$")


def retrieve_locations() -> Dict[str, Dict[str, list]]:
    """
    Retrieve mullvad locations from the CLI

    Returns
    -------
    mullvad locations: Dict[country, Dict[city, list_of_servers]]
    """

    location_list = subprocess.run(["mullvad", "relay", "list"], capture_output=True)
    location_str = io.StringIO(location_list.stdout.decode("UTF-8"))
    location_dict = defaultdict(lambda: defaultdict(list))

    current_country = None
    current_city = None

    for line in location_str:
        if match := regex_country.match(line):
            current_country = match.group(1)
            continue

        if match := regex_city.match(line):
            current_city = match.group(1)
            continue

        if match := regex_server.match(line):
            location_dict[current_country][current_city].append(match.group(1))
            continue

    return location_dict


def get_random_location(location_list: dict = None) -> str:
    """
    Select a random server from mullvad server list

    Parameters
    ----------
    location_list: dict
        mullvad server list organized by country and city

    Returns
    -------
    mullvad server: str

    """

    flatten_locations = [
        server
        for country, city_dict in location_list.items()
        for city, server_list in city_dict.items()
        for server in server_list
    ]

    random.shuffle(flatten_locations)

    return flatten_locations.pop()


def get_connection_status() -> Union[str, None]:
    """
    Get mullvad connection status

    Returns
    -------
    mullvad server or None if not connected
    """

    status_call = subprocess.run(["mullvad", "status"], capture_output=True)

    status_str = io.StringIO(status_call.stdout.decode("UTF-8"))
    status_str = status_str.readlines()[0]

    status = regex_status.match(status_str).group(1)

    if status == "Disconnected":
        return None

    elif status == "Connected":
        server = regex_status_server.match(status_str).group(1)

        return server


def disconnect() -> None:
    _ = subprocess.run(["mullvad", "disconnect"])


def connect() -> None:
    _ = subprocess.run(["mullvad", "connect"])


def connect_to_random_server():
    # mullvad relay set hostname se-mma-001

    if get_connection_status() is not None:
        disconnect()

    location_list = retrieve_locations()
    random_server = get_random_location(location_list=location_list)

    setting_status = subprocess.run(
        ["mullvad", "relay", "set", "hostname", random_server], capture_output=True
    )

    setting_status_str = io.StringIO(setting_status.stdout.decode("UTF-8"))
    setting_status_str = setting_status_str[-1]

    if regex_set_server.match(setting_status_str) is None:
        raise Exception("Impossible to set the server")

    connect()
