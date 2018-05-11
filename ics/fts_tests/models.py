

def customize_INSTALLED_APPS(local_vars):
    # TODO: mover de 'models' a otro modulo
    local_vars['INSTALLED_APPS'] += (
        'fts_tests',
    )
