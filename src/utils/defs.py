def enum(**enums):
    return type('Enum', (), enums)

JOB_STATES = enum(
    available='AVAILABLE',
    claimed='CLAIMED',
    started='STARTED',
    finished='FINISHED',
    failed='FAILED')
