import json
import os

def generate_report():
    input_file = "data/simulation_results.json"
    output_file = "docs/docs/simulation-results.md"
    
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found. Run mass_simulation.py first.")
        return
        
    with open(input_file, 'r') as f:
        data = json.load(f)
        
    markdown = [
        "# Simulation Statistical Report",
        "",
        "This report analyzes the survivability, identity retention, and overall ethical standing of 5 allegorical societal groups across multiple environmental scenarios (100 runs per scenario).",
        "",
        "## Analyzed Groups",
        "- **The Share-Bears**: High Altruism, High Kinship, Low Efficiency.",
        "- **The Cog-Workers**: Neutral Altruism, Very High Efficiency.",
        "- **The Iron-Fists**: Very Low Altruism (High Egoism), High Aggression.",
        "- **The Free-Traders**: Low Altruism, High Efficiency, High Exploration.",
        "- **The Hive-Mind**: Maximum Altruism, Shared Efficiency.",
        ""
    ]
    
    overall_survivability = {
        "Share-Bears": 0, "Cog-Workers": 0, "Iron-Fists": 0, "Free-Traders": 0, "Hive-Mind": 0
    }
    
    for scenario, runs in data.items():
        markdown.append(f"## Scenario: {scenario.capitalize()}")
        
        scenario_survivors = {g: 0 for g in overall_survivability.keys()}
        total_mixed = 0
        total_altruism = 0
        
        for run in runs:
            total_mixed += run["mixed_breeds"]
            total_altruism += run["average_altruism"]
            for g, count in run["survivors_by_group"].items():
                scenario_survivors[g] += count
                overall_survivability[g] += count
                
        avg_mixed = total_mixed / len(runs)
        avg_altruism = total_altruism / len(runs)
        
        markdown.append("### Survival Counts (Total across 100 runs)")
        for g, count in scenario_survivors.items():
            markdown.append(f"- **{g}**: {count}")
            
        markdown.append("")
        markdown.append(f"**Average Mixed Breeds (Identity Loss)**: {avg_mixed:.2f} per run")
        markdown.append(f"**Average Global Altruism**: {avg_altruism:.2f}")
        markdown.append("")

    markdown.append("## Conclusion & Ethical Analysis")
    markdown.append("")
    
    # Calculate the most survivable
    most_survivable = max(overall_survivability, key=overall_survivability.get)
    
    markdown.append(f"### The Survival Winner: **{most_survivable}**")
    markdown.append(f"The {most_survivable} proved to be the most numerically resilient across all environments.")
    markdown.append("")
    
    # Determine the most "ethical" to be in without compromising identity
    # For this simulation, we define "ethical" as a group that survives well AND has high altruism (cares for its weak).
    # Since we know the base altruism of the groups from config.py:
    # Share-Bears: 0.9, Hive-Mind: 1.0, Cog-Workers: 0.5, Free-Traders: 0.3, Iron-Fists: 0.1
    
    base_altruism = {
        "Share-Bears": 0.9, "Cog-Workers": 0.5, "Iron-Fists": 0.1, "Free-Traders": 0.3, "Hive-Mind": 1.0
    }
    
    # Calculate an 'Ethical Score' = (Total Survivors / Max Survivors) * Base Altruism
    max_survivors = max(overall_survivability.values())
    
    ethical_scores = {}
    for g in overall_survivability.keys():
        surv_ratio = overall_survivability[g] / max_survivors if max_survivors > 0 else 0
        ethical_scores[g] = surv_ratio * base_altruism[g]
        
    most_ethical = max(ethical_scores, key=ethical_scores.get)
    
    markdown.append(f"### The Most Ethical & Safe Group: **{most_ethical}**")
    markdown.append(f"By weighting the raw survivability against the group's inherent altruism (willingness to share resources with the weak and young), the **{most_ethical}** emerges as the most ethical group to join without severely compromising one's safety.")
    
    with open(output_file, 'w') as f:
        f.write("\n".join(markdown))
        
    print(f"Report generated at {output_file}")

if __name__ == "__main__":
    generate_report()
