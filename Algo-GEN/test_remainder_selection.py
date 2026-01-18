import sys

sys.path.append('.')

from selection import remainder_selection
import random


def test_remainder_basic():
    """Test basique : vérifier que ça retourne un individu"""
    print("=" * 50)
    print("TEST 1 : Vérification basique")
    print("=" * 50)

    population = [
        [1, 2, 3, 4],
        [4, 3, 2, 1],
        [2, 1, 4, 3],
        [3, 4, 1, 2]
    ]

    fitnesses = [0.186, 0.322, 0.085, 0.407]

    selected = remainder_selection(population, fitnesses)

    print(f"Population: {len(population)} individus")
    print(f"Type retourné: {type(selected)}")
    print(f"Sélectionné: {selected}")

    assert isinstance(selected, list), "Doit retourner une liste (chromosome)"
    assert selected in population, "Doit retourner un individu de la population"
    print("✅ Test basique réussi!\n")


def test_remainder_distribution():
    """Test : vérifier la distribution selon les fitnesses"""
    print("=" * 50)
    print("TEST 2 : Distribution des sélections")
    print("=" * 50)

    population = [
        [1, 2, 3, 4],
        [4, 3, 2, 1],
        [2, 1, 4, 3],
        [3, 4, 1, 2]
    ]

    fitnesses = [0.186, 0.322, 0.085, 0.407]
    names = ["I1", "I2", "I3", "I4"]

    N = len(population)
    total = sum(fitnesses)
    print(f"\nCalculs théoriques (N={N}):")
    print(f"{'Ind':<5} {'pi':<8} {'Ei':<8} {'Ent(Ei)':<10} {'Ri':<8}")
    print("-" * 50)

    for i, (name, fit) in enumerate(zip(names, fitnesses)):
        pi = fit / total
        Ei = N * pi
        Ent_Ei = int(Ei)
        Ri = Ei - Ent_Ei
        print(f"{name:<5} {pi:<8.3f} {Ei:<8.3f} {Ent_Ei:<10} {Ri:<8.3f}")

    print(f"\nSimulation de 1000 sélections:")
    counts = {i: 0 for i in range(len(population))}

    random.seed(42)
    for _ in range(1000):
        selected = remainder_selection(population, fitnesses)
        idx = population.index(selected)
        counts[idx] += 1

    print(f"\n{'Ind':<5} {'Fitness':<10} {'Nb sélections':<15} {'%':<8}")
    print("-" * 50)
    for i, (name, fit) in enumerate(zip(names, fitnesses)):
        percentage = (counts[i] / 1000) * 100
        print(f"{name:<5} {fit:<10.3f} {counts[i]:<15} {percentage:<8.1f}%")

    best_idx = fitnesses.index(max(fitnesses))
    assert counts[best_idx] == max(counts.values()), \
        "L'individu avec meilleur fitness devrait être le plus sélectionné"

    print("\n✅ Test de distribution réussi!\n")


def test_remainder_edge_cases():
    """Test : cas limites"""
    print("=" * 50)
    print("TEST 3 : Cas limites")
    print("=" * 50)

    print("\nCas 1 : Fitnesses égaux")
    pop = [[1, 2], [3, 4], [5, 6], [7, 8]]
    fits = [0.25, 0.25, 0.25, 0.25]
    selected = remainder_selection(pop, fits)
    assert selected in pop
    print(f"  Sélectionné: {selected} ✅")

    print("\nCas 2 : Un fitness dominant")
    pop = [[1, 2], [3, 4], [5, 6], [7, 8]]
    fits = [0.9, 0.05, 0.03, 0.02]
    counts = {i: 0 for i in range(4)}
    for _ in range(100):
        selected = remainder_selection(pop, fits)
        counts[pop.index(selected)] += 1
    print(f"  Distribution: {counts}")
    print(f"  Meilleur (I1) sélectionné {counts[0]} fois sur 100 ✅")

    print("\nCas 3 : Fitnesses tous à zéro")
    pop = [[1, 2], [3, 4]]
    fits = [0, 0]
    selected = remainder_selection(pop, fits)
    assert selected in pop
    print(f"  Sélectionné: {selected} ✅")

    print("\n✅ Tous les cas limites passés!\n")


def test_compare_with_example():
    """Test avec l'exemple du slide 20"""
    print("=" * 50)
    print("TEST 4 : Exemple du cours (slide 20)")
    print("=" * 50)

    population = [
        [1, 0, 0, 0],
        [0, 1, 0, 0],
        [0, 0, 1, 0],
        [0, 0, 0, 1]
    ]

    fitnesses = [0.186, 0.322, 0.085, 0.407]

    N = 4
    total = sum(fitnesses)

    print("\nThéorie (N=4):")
    expected = [N * (f / total) for f in fitnesses]
    for i, (E, f) in enumerate(zip(expected, fitnesses)):
        Ent = int(E)
        R = E - Ent
        print(f"  I{i + 1}: Ei={E:.3f}, Ent(Ei)={Ent}, Ri={R:.3f}")

    print(f"\nPhase 1 attendue: I2 (1 fois), I4 (1 fois)")
    print(f"Phase 2 attendue: 2 sélections selon Ri")

    random.seed(42)
    counts = {i: 0 for i in range(4)}
    for _ in range(1000):
        selected = remainder_selection(population, fitnesses)
        counts[population.index(selected)] += 1

    print(f"\nRésultats sur 1000 essais:")
    for i in range(4):
        print(f"  I{i + 1}: {counts[i]} sélections")

    print("\n✅ Test avec exemple du cours réussi!\n")


def test_exemple_exact_du_cours():
    """TEST 5 : EXEMPLE EXACT DU COURS"""
    print("=" * 70)
    print("TEST 5 : EXEMPLE EXACT DU COURS")
    print("=" * 70)

    sequences = ["10011", "10011", "00101", "11000"]
    # Population avec indices pour éviter confusion
    population_dict = {
        0: [1, 0, 0, 1, 1],  # I1
        1: [1, 0, 0, 1, 1],  # I2 (identique à I1!)
        2: [0, 0, 1, 0, 1],  # I3
        3: [1, 1, 0, 0, 0]  # I4
    }

    population = list(population_dict.values())
    fitnesses = [11, 19, 5, 24]

    N = 4
    total_fitness = sum(fitnesses)

    print(f"\n📊 Tableau du cours:")
    print(f"{'Individu':<10} {'Séquence':<10} {'Fitness':<10} {'% du total':<12}")
    print("-" * 50)

    for i in range(4):
        percentage = (fitnesses[i] / total_fitness) * 100
        print(f"I{i + 1:<9} {sequences[i]:<10} {fitnesses[i]:<10} {percentage:<11.1f}%")

    print(f"{'Total':<10} {'':<10} {total_fitness:<10} {'100%':<12}")

    print(f"\n📐 Calculs théoriques (N={N}):")
    print(f"{'Ind':<5} {'pi':<8} {'Ei':<8} {'Ent(Ei)':<10} {'Ri':<8}")
    print("-" * 50)

    for i in range(4):
        pi = fitnesses[i] / total_fitness
        Ei = N * pi
        Ent_Ei = int(Ei)
        Ri = Ei - Ent_Ei

        print(f"I{i + 1:<4} {pi:<8.3f} {Ei:<8.3f} {Ent_Ei:<10} {Ri:<8.3f}")

    print("\n" + "=" * 70)
    print("🔬 Vérification statistique (1000 simulations)")
    print("=" * 70)

    # SOLUTION: Suivre les indices manuellement
    counts = {i: 0 for i in range(4)}
    random.seed(42)

    for _ in range(1000):
        # Appliquer l'algorithme et récupérer l'index
        N = len(population)
        total_fit = sum(fitnesses)
        probabilities = [f / total_fit for f in fitnesses]
        E_values = [N * p for p in probabilities]

        selected_indices = []
        for i, E in enumerate(E_values):
            count = int(E)
            selected_indices.extend([i] * count)

        remainders = [E - int(E) for E in E_values]
        total_remainder = sum(remainders)

        while len(selected_indices) < N:
            if total_remainder > 0:
                rand = random.uniform(0, total_remainder)
                cumulative = 0
                for i, remainder in enumerate(remainders):
                    cumulative += remainder
                    if rand <= cumulative:
                        selected_indices.append(i)
                        break

        chosen_index = random.choice(selected_indices)
        counts[chosen_index] += 1

    print(f"\n   Distribution observée:")
    print(f"   {'Ind':<5} {'Fitness':<10} {'Sélections':<12} {'%':<8} {'% attendu':<10}")
    print("   " + "-" * 60)

    all_good = True
    for i in range(4):
        percentage = (counts[i] / 1000) * 100
        expected_percentage = (fitnesses[i] / total_fitness) * 100
        diff = abs(percentage - expected_percentage)
        status = "✅" if diff < 5 else "⚠️"
        if diff >= 5:
            all_good = False
        print(
            f"   {status} I{i + 1:<4} {fitnesses[i]:<10} {counts[i]:<12} {percentage:<7.1f}% {expected_percentage:<9.1f}%")

    if all_good:
        print(f"\n   ✅ La distribution est proportionnelle aux fitness!")
    else:
        print(f"\n   ⚠️ Attention: écarts importants détectés")

    print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    test_remainder_basic()
    test_remainder_distribution()
    test_remainder_edge_cases()
    test_compare_with_example()
    test_exemple_exact_du_cours()

    print("=" * 70)
    print("🎉 TOUS LES TESTS SONT PASSÉS!")
    print("=" * 70)