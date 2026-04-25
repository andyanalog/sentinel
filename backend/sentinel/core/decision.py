from sentinel.models.evaluation import Action

ALLOW_THRESHOLD = 40
BLOCK_THRESHOLD = 65


def decide(score: int) -> Action:
    if score >= BLOCK_THRESHOLD:
        return Action.BLOCK
    if score >= ALLOW_THRESHOLD:
        return Action.CHALLENGE
    return Action.ALLOW
