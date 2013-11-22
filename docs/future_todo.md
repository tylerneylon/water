# Future todo items
Things I'm interested in doing eventually, but which are not time critical.

## Delayed parse actions.

This idea is to take parse actions only after a phrase has been completely
parsed. This idea would make much more sense if we disallow mode parsing
failures, since, intuitively, that would avoid long delays. One point of
difficulty are things like substitutions, or parse_string executions which
we want to happen along the way. At first, I thought such intermediate
actions would make this very difficult, but now I'm not so sure, and I think
it's worth aiming for.
