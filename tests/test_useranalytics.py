from user_analytics import UserAnalytics


def test_module_and_levels_per_module():
    logs = {
        'LEVEL': ['INFO', 'DEBUG', 'ERROR', 'INFO', 'WARN', 'DEBUG'],
        'MODULE': ['mod.a', 'mod.a', 'mod.b', 'mod.c', 'mod.a', 'mod.b'],
    }

    ua = UserAnalytics(logs)
    module_counts = ua.calculate_module_stats()
    assert module_counts['mod.a'] == 3
    assert module_counts['mod.b'] == 2
    assert module_counts['mod.c'] == 1

    levels_per = ua.calculate_levels_per_module()
    assert levels_per['mod.a']['INFO'] == 1
    assert levels_per['mod.a']['DEBUG'] == 1
    assert levels_per['mod.b']['ERROR'] == 1
    assert levels_per['mod.b']['DEBUG'] == 1
    assert levels_per['mod.c']['INFO'] == 1
