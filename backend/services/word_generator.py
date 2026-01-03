import random
from typing import Set, List


class WordGenerator:
    WORDS = [
        "cat",
        "dog",
        "house",
        "tree",
        "car",
        "fish",
        "flower",
        "sun",
        "star",
        "apple",
        "banana",
        # "bird",
        "butterfly",
        # "circle",
        # "square",
        "airplane",
        "axe",
        "basketball",
        "bed",
        "bee",
        "bicycle",
        "camera",
        "cake",
        "dragon",
        # "elephant",
        "face",
        "fork",
        "hamburger",
        "hat",
        "helicopter",
        "hourglass",
        "mushroom",
        "nose",
        # "octagon",
        "pencil",
        "piano",
        "radio",
        "scissors",
        "shorts",
        "skateboard",
        "snowflake",
        "snowman",
        "spoon",
        "strawberry",
        "vase",
        "watermelon",
        "wheel",
        "zebra",
        "zigzag",
        "umbrella",
    ]

    
    def __init__(self):
        self._used_words: Set[str] = set()
    
    def get_random_word(self, exclude: Set[str] = None) -> str:
        if exclude is None:
            exclude = set()
        
        available = [w for w in self.WORDS if w not in exclude]
        
        if not available:
            available = self.WORDS
        
        return random.choice(available)
    
    def get_words_for_game(self, count: int) -> List[str]:
        available = self.WORDS.copy()
        random.shuffle(available)
        return available[:count]
    
    def reset(self) -> None:
        self._used_words.clear()


word_generator = WordGenerator()
