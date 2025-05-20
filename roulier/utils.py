# Copyright 2025 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


def split_address(addresses, max_length=64, address_count=2):
    """
    Split an address part list `addresses` into an `address_count` number of
    parts, each with a maximum length of `max_length`.

    :param addresses: The list of address parts to split.
    :param max_length: The maximum length of each address part.
    :param address_count: The number of address parts to split into.
    :return: A list of address parts of length `address_count`

    >>> split_address(['45 rue de la paix', '75002 Paris'], 12, 2)
    ['45 rue de la', 'paix', '75002 Paris']

    >>> split_address(['45 rue de la paix', '75002 Paris'], 14, 2)
    ['45 rue de la', 'paix', '75002 Paris']

    >>> split_address(['45 rue de la paix', '75002 Paris'], 12, 3)
    ['45 rue de la paix', '75002 Paris', '']

    >>> split_address(['45 rue de la paix', '75002 Paris'], 6, 5)
    ['45 rue', 'de la', 'paix', '75002', 'Paris']

    >>> split_address(['45 rue de la paix', '75002 Paris'], 6, 4)
    ['45 rue', 'de la', '75002', 'Paris']

    >>> split_address(['45 rue de la paix', '75002 Paris'], 6, 2)
    ['45 rue', '75002']
    """
    result = []
    current_part = []
    current_length = 0

    for address in addresses:
        for word in (address or "").split():
            if current_length + len(word) + (1 if current_part else 0) > max_length:
                result.append(" ".join(current_part))
                current_part = []
                current_length = 0
                if len(result) == address_count - 1:
                    result.append("")
                    break
            current_part.append(word)
            current_length += len(word) + (1 if current_part else 0)

        if len(result) == address_count - 1:
            break

    if current_part:
        result.append(" ".join(current_part))

    while len(result) < address_count:
        result.append("")

    return result[:address_count]


def split_partner_address(partner, max_length=32, address_count=2):
    """
    Split a partner address into a list of address parts.

    :param partner: The partner object to split the address from.
    :param max_length: The maximum length of each address part.
    :param address_count: The number of address parts to split into.
    :return: A list of address parts of length `address_count`
    """
    addresses = [
        partner.street,
        partner.street2,
    ]
    return {
        f"street{i + 1}": part
        for i, part in enumerate(split_address(addresses, max_length, address_count))
    }
