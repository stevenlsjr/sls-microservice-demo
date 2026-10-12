import os


def get_kafka_options(env=os.environ, strip_blank: bool = False):
    options = {}
    for k in env:
        transformed_key = k.lower()
        if not transformed_key.startswith("kafka__"):
            continue
        option_path = transformed_key.split("__")[1:]  # remove kafka
        option_key = ".".join(option_path)
        value = env[k]
        if value or not strip_blank:
            options[option_key] = env[k]

    return options

