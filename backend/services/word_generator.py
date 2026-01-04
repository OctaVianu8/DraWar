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
        "butterfly",
        "airplane",
        "axe",
        "basketball",
        "bed",
        "bee",
        "bicycle",
        "camera",
        "cake",
        "dragon",
        "face",
        "fork",
        "hamburger",
        "hat",
        "helicopter",
        "hourglass",
        "mushroom",
        "nose",
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
        self._shuffled_deck: List[str] = []
        self._reshuffle()
    
    def _reshuffle(self) -> None:
        self._shuffled_deck = self.WORDS.copy()
        random.shuffle(self._shuffled_deck)
    
    def get_random_word(self, exclude: Set[str] = None) -> str:
        if exclude is None:
            exclude = set()
        
        for _ in range(len(self.WORDS)):
            if not self._shuffled_deck:
                self._reshuffle()
            
            word = self._shuffled_deck.pop()
            
            if word not in exclude:
                return word
        
        if not self._shuffled_deck:
            self._reshuffle()
        return self._shuffled_deck.pop()
    
    def get_words_for_game(self, count: int) -> List[str]:
        words = []
        for _ in range(count):
            words.append(self.get_random_word(exclude=set(words)))
        return words
    
    def reset(self) -> None:
        self._reshuffle()


word_generator = WordGenerator()
