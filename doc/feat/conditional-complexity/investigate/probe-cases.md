# One-time probe inputs

These snippets record the bounded syntax inputs used for the 8.0.1 observations
in [findings](findings.md). They are execution records, not retained upstream
algorithm tests.

## Complexipy cases

```text
def boolean_chain(a, b, c, d, e, f):
    if a and b and c and d and e and f:
        return True
    return False

def nested_and_flat(a, b, c):
    if a:
        if b:
            if c:
                return 1
    if a:
        return 2
    if b:
        return 3
    if c:
        return 4
    return 0

def elif_chain(value):
    if value == 1:
        return "one"
    elif value == 2:
        return "two"
    elif value == 3:
        return "three"
    else:
        return "other"

def match_guard(value, enabled, ready):
    match value:
        case "one" if enabled and ready:
            return 1
        case "two":
            return 2
        case _:
            return 0

def quantified(values):
    if all(value.valid and value.ready for value in values):
        return [value.name for value in values if value.valid and value.ready]
    return []

def helper_extraction(user):
    if user is None:
        return False
    if user.active and user.verified and user.has_access:
        return True
    return False

def alternate_extraction(user):
    return _eligible(user)

def _eligible(user):
    return user is not None and user.active and user.verified and user.has_access

def non_if_boolean_forms(a, b, c, values):
    while a and b and c:
        break
    assert a and b and c
    return a and b and c, [item for item in values if item and a and b and c]
```

## Ruff PLR0916 cases

```text
def conditional_if(a, b, c, d, e, f):
    if a and b and c and d and e and f:
        return True
    return False

def conditional_elif(a, b, c, d, e, f):
    if a:
        return True
    elif a and b and c and d and e and f:
        return True
    return False

def while_guard(a, b, c, d, e, f):
    while a and b and c and d and e and f:
        break
    return False

def assert_guard(a, b, c, d, e, f):
    assert a and b and c and d and e and f

def conditional_expression(a, b, c, d, e, f):
    return True if a and b and c and d and e and f else False

def comprehension_guard(values, a, b, c, d, e, f):
    return [value for value in values if a and b and c and d and e and f]

def match_guard(value, a, b, c, d, e, f):
    match value:
        case _ if a and b and c and d and e and f:
            return True
        case _:
            return False
```
