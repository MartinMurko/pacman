This is my bot for the pacman competition.

Implemented features:

ATTACKER:
    Goes for the nearest food.

    Treats visible enemy ghosts as dangerous unless they're scared.

    Heads home to bank food under certain conditions.

    While running home from a ghost, it goes to a capsule if one is closer than home.

    If a ghost is close and it's carrying nothing, it goes for a capsule.

    If every path is blocked, it runs away from the ghosts.

DEFENDER:
    Guards a border square chosen at game start: the one closest overall to the food it defends.

    Notices when your food disappears and goes there.

    Chases the nearest visible invader.

    When it's scared, it runs away from attacker.


TO DO: 
    Strategy rather than greedy.

    Dead ends.

    Attacker chasing ghsots when they are scared.

    Dynamic roles rather than only attack/defense.

    Eat more food and far away, when they are scared.

    Use noisy distance readings also.

    Tune some settings.