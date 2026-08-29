# Configuration file for predefined societal groups (DNA setups)

ALLEGORICAL_GROUPS = {
    "Share-Bears": {
        "description": "High Altruism, High Kinship, Low Individual Efficiency.",
        "color": (255, 105, 180), # Hot Pink
        "shape": "D20",
        # DNA: [Altruism, Resource Efficiency, Exploration Rate, Reproduction Urge, Speed]
        "dna": [0.9, 0.4, 0.3, 0.6, 0.4] 
    },
    "Cog-Workers": {
        "description": "Neutral Altruism, Very High Efficiency, High Exploration.",
        "color": (0, 255, 255), # Cyan
        "shape": "D6",
        "dna": [0.5, 0.9, 0.8, 0.4, 0.7]
    },
    "Iron-Fists": {
        "description": "Very Low Altruism (High Egoism), High Aggression/Speed, Low Kinship.",
        "color": (50, 50, 50), # Dark Grey
        "shape": "D4",
        "dna": [0.1, 0.6, 0.9, 0.7, 0.9]
    },
    "Free-Traders": {
        "description": "Low Altruism, High Efficiency, High Exploration.",
        "color": (255, 215, 0), # Gold
        "shape": "D8",
        "dna": [0.3, 0.8, 0.9, 0.6, 0.8]
    },
    "Hive-Mind": {
        "description": "Maximum Altruism, Zero Egoism, Shared Efficiency.",
        "color": (128, 0, 128), # Purple
        "shape": "D12",
        "dna": [1.0, 0.7, 0.2, 0.9, 0.5]
    }
}
