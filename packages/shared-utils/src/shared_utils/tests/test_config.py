from .. import config


def test_get_kafka_options():
    env = {
        'KAFKA__CLIENT__ID': 'foo',
        'KAFKA__BATCH__SIZE': '1000'
    }
    expected = {
        'client.id': 'foo',
        'batch.size': '1000'
    }
    assert config.get_kafka_options(env) == expected

    env = {
            'KAFKA__CLIENT__ID': 'foo',
            'KAFKA__BATCH__SIZE': '1000',
            'KAFKA__BLANK_OPTION': ""
        }
    assert config.get_kafka_options(env, strip_blank=True) == expected, 'strip blank env options'
    assert config.get_kafka_options(env, strip_blank=False) == (expected | {'blank_option': ''}), 'strip blank env options'
