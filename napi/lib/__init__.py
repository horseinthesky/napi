def _flatten(vlans: str) -> list[int]:
    return [
        num
        for group in vlans.split(",")
        for a, _, b in [group.partition("-")]
        for num in range(int(a), int(b or a) + 1)
    ]


def _mac_dash_to_column(mac):
    return ":".join(
        [
            piece
            for block in mac.split("-")
            for piece in [block[:2], block[2:]]
        ]
    )
