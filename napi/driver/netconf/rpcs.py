capabilities = [
    "urn:ietf:params:netconf:base:1.0",
]

hello = {
    "hello": {
        "@xmlns": "urn:ietf:params:xml:ns:netconf:base:1.0",
        "capabilities": {
            "capability": None,
        },
    }
}

close = {
    "rpc": {
        "@message-id": "1",
        "@xmlns": "urn:ietf:params:xml:ns:netconf:base:1.0",
        "close-session": None,
    }
}

get = {
    "rpc": {
        "@message-id": "1",
        "@xmlns": "urn:ietf:params:xml:ns:netconf:base:1.0",
        "get": {},
    }
}

get_config = {
    "rpc": {
        "@message-id": "1",
        "@xmlns": "urn:ietf:params:xml:ns:netconf:base:1.0",
        "get-config": {},
    }
}

edit_config = {
    "rpc": {
        "@message-id": "1",
        "@xmlns": "urn:ietf:params:xml:ns:netconf:base:1.0",
        "edit-config": None,
    }
}

commit = {
    "rpc": {
        "@message-id": "1",
        "@xmlns": "urn:ietf:params:xml:ns:netconf:base:1.0",
        "commit": None,
    }
}
