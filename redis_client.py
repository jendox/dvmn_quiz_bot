from redis import Redis


def connect_redis(
    host: str,
    port: int,
    username: str,
    password: str,
) -> Redis:
    return Redis(
        host=host,
        port=port,
        username=username,
        password=password,
        decode_responses=True,
    )
