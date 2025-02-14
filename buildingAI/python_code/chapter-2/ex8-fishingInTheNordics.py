def main():
    countries = ['Denmark', 'Finland', 'Iceland', 'Norway', 'Sweden']
    populations = [5615000, 5439000, 324000, 5080000, 9609000]
    fishers = [1891, 2652, 3800, 11611, 1757]

    total_fishers = sum(fishers)
    total_population = sum(populations)

    # Calculate P(Country|Fisher) = P(Fisher|Country) * P(Country) / P(Fisher)
    # = (fishers[i]/populations[i]) * (populations[i]/total_population) / (total_fishers/total_population)
    # Simplifies to: fishers[i]/total_fishers
    probabilities = [fisher/total_fishers * 100 for fisher in fishers]

    for country, prob in zip(countries, probabilities):
        print("%s %.2f%%" % (country, prob)) # modify this to print correct results

main()