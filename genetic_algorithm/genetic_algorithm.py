"""Author: Jakub Gnyp; contact: gnyp.jakub@gmail.com, LinkedIn: https://www.linkedin.com/in/gnypit/"""
import random
from numpy.random import binomial as np_binom
from numpy import floor

identification = 0


def sort_dict_by_fit(dictionary):
    return dictionary['fitness value']


class Chromosome:
    def __init__(self, genes):
        self.genes = genes  # a dictionary

        """Optional fields, that I'm not sure I'll use directly in the Chromosome:"""
        self.fit_fun = None
        self.fit_val = None

    def __repr__(self) -> str:
        return f"{type(self).__name__}(genes={self.genes}, fitness function={self.fit_fun}, fitness value={self.fit_val})"

    def change_genes(self, genes):
        self.genes = genes

    def evaluate(self, fitness_function):
        self.fit_fun = fitness_function
        self.fit_val = self.fit_fun(self.genes)

    def __iter__(self):  # might be redundant
        return self


class Member(Chromosome):
    def __init__(self, genes, identification_number):
        super().__init__(genes)
        self.id = identification_number
        self.parents_id = None

    def add_parents_id(self, parents_id):  # it's meant for 'genealogical tree' tracking
        self.parents_id = parents_id  # it's a list with IDs of the parents

    def __repr__(self) -> str:
        return f"{type(self).__name__}(genes={self.genes}, id={self.id}, parents_id={self.parents_id})"


class Generation:
    def __init__(self, size, genome_generator=None, args=None):
        """genome_generator is the function that creates genomes for the initial generation
        of population members, args are arguments to be used in genome_generator;
        this method uses a global variable identification for creating unique IDs for created members"""

        global identification
        self.size = size
        self.members = []
        self.genome_generator = genome_generator
        self.genome_generator_args = args

        if self.genome_generator is not None:
            for index in range(self.size):
                new_member = Member(self.genome_generator(self.genome_generator_args), identification)
                identification += 1
                self.members.append(new_member)

    def add_member(self, genome, parents_id=None):
        """Method for manual creation of new members"""

        global identification
        new_member = Member(genes=genome, identification_number=identification)

        if parents_id is not None:
            new_member.add_parents_id(parents_id=parents_id)

        self.members.append(new_member)
        identification += 1


"""At this point we need to define crossover operators"""


def single_point_crossover(crossover_point, parent1, parent2):
    """Parents will be crossed such that genes from first one (numbered from 0) up to crossover_point
    included shall go to one child, and the rest to the other."""

    parent1_genes = list(parent1.genes)
    parent2_genes = list(parent2.genes)

    # TODO: different working with genes whether it's a dict or a list

    gene_counter = 0
    child1_genes = []
    child2_genes = []

    while gene_counter <= crossover_point:
        child1_genes.append(parent1_genes[gene_counter])
        child2_genes.append(parent2_genes[gene_counter])
        gene_counter += 1

    while gene_counter < len(parent1_genes):
        child1_genes.append(parent2_genes[gene_counter])
        child2_genes.append(parent1_genes[gene_counter])
        gene_counter += 1

    # child1 = Chromosome()
    # child2 = Chromosome()

    return [child1_genes, child2_genes]


def uniform_crossover(parent1, parent2, choice_prob=0.5):
    """In this crossover method a gene mask is randomised. By default, there is 2 children. For the first one
    0 indicates genes from the first parent, while 1 - from the second one. For the second one contrarily.

    no_kids specifies how many children are to be breaded;

    choice_prob is the probability of choosing a gene from the first parent in a single Bernoulli trial.
    """
    parent1_genes = list(parent1.genes)
    parent2_genes = list(parent2.genes)

    # TODO: different working with genes whether it's a dict or a list

    child1_genes = []
    child2_genes = []

    gene_mask = np_binom(1, 1 - choice_prob, len(parent1_genes))
    index = 0

    for indicator in gene_mask:
        if indicator == 0:
            child1_genes.append(parent1_genes[index])
            child2_genes.append(parent2_genes[index])
        else:
            child1_genes.append(parent2_genes[index])
            child2_genes.append(parent1_genes[index])
        index += 1

    # child1 = Chromosome()
    # child2 = Chromosome()

    return [child1_genes, child2_genes]


def plco(parent1, parent2, transit_point, alfa=0.5, beta=0.5):  # partially linear crossover operator, my idea
    """Two children are created; integer-valued genes are exchanged as in single crossover operator,
    while the real-valued genes are linearly combined using formula:

    child_gene = alfa * parent1_gene + beta * parent2_gene

    transit point is the index from which crossover is linear; beforehand it's single point
    """
    parent1_genes = list(parent1.genes)
    parent2_genes = list(parent2.genes)
    no_genes = len(parent1_genes)

    # TODO: different working with genes whether it's a dict or a list

    child1_genes = []
    child2_genes = []

    for index in range(transit_point // 2 + 1):  # single-point crossover part 1
        child1_genes.append(parent1_genes[index])
        child2_genes.append(parent2_genes[index])
    for index in range(transit_point // 2 + 1, transit_point):  # single-point crossover part 2
        child1_genes.append(parent2_genes[index])
        child2_genes.append(parent1_genes[index])
    for index in range(transit_point, no_genes):  # linear crossover
        child1_genes.append(alfa * parent1_genes[index] + beta * parent2_genes[index])
        child2_genes.append(alfa * parent2_genes[index] + beta * parent1_genes[index])

    return [child1_genes, child2_genes]


class Population:
    def __init__(self, pop_size, fit_fun, genome_generator, args, elite_size, mutation_prob=0.0, seed=None):
        """pop_size is a constant size of the population, fit_fun is a chosen fitness function to be used in a
        genetic algorithm, genom_generator is the function that creates genomes for the initial generation
        of population members, args are arguments to be used in genom_generator, mutation_prob is a probability
        of a single member's genome being initialised from scratch, seed is for pseud-random number generation."""

        if seed is not None:
            random.seed(a=seed)  # temporary, for debugging

        self.pop_size = pop_size
        self.elite_size = elite_size
        self.mutation_prob = mutation_prob
        self.fit_fun = fit_fun
        self.current_generation = Generation(size=pop_size, genome_generator=genome_generator, args=args)
        self.generations = [self.current_generation]
        self.current_parents = []
        self.current_children = []

        """What we need is to be able to sort whole generation based on fitness values AND remember chromosomes 
        indexes in their (generation) list in order to be able to crossbreed them with each other based on the
        fitness ranking. Thus, for each generation we create a list of dictionaries for this ranking. 
        These dictionaries shall have just two keys: index (of a chromosome) and a fitness value 
        (of the same chromosome). Once we compute such a fitness ranking for the whole generation, 
        we shall sort it using sort_dict_by_fit function.
        """

        self.fitness_rankings = []
        self.current_fitness_ranking = None

    def evaluate_generation(self, reverse=True):  # true for sorting from the highest fitness value to the lowest
        """This method applies the fitness function to the current generation and sorts the fitness ranking by
        the fitness values of current generation's members - 'reverse' means sorting will be performed
        from maximum fitness to minimum."""
        self.current_fitness_ranking = []

        for i in range(len(self.current_generation.members)):
            self.current_fitness_ranking.append(
                {'index': i, 'fitness value': self.fit_fun(self.current_generation.members[i])}
            )

        self.current_fitness_ranking.sort(key=sort_dict_by_fit, reverse=reverse)
        self.fitness_rankings.append(self.current_fitness_ranking)

    def best_fit(self):  # we return gene sequence of the chromosome of the highest fitness value with it's fit value
        bf = [self.current_generation.members[self.current_fitness_ranking[0].get('index')].genes,
              self.current_fitness_ranking[0].get('fitness value')]
        return bf

    def ranking_selection(self):  # deterministic
        """We use 'member_counter' as an index for the fitness ranking. While it's smaller than the elite
        size for the whole population, we simply copy-paste the old members into the new generation. That's why
        we automatically calculate it and focus on selecting pairs of members from the current generation as parents
        for crossover performed later. Only then will the 'elite' members be copy-pasted."""
        member_counter = 2 * self.elite_size

        """
        while member_counter < self.elite_size:
            self.current_parents.append(
                self.current_generation[self.current_fitness_ranking[member_counter].get('index')]
            )
            self.current_parents.append(
                self.current_generation[self.current_fitness_ranking[member_counter + 1].get('index')]
            )
            member_counter += 2
        """

        """As every other one, this selection operator creates his own list of candidates for parents of the future
        generation from the current generation and appends it to the 'parents' field in this class:"""
        parents_candidates = []

        while member_counter < self.current_generation.size:
            parent1 = self.current_generation.members[self.current_fitness_ranking[member_counter].get('index')]
            parent2 = self.current_generation.members[self.current_fitness_ranking[member_counter + 1].get('index')]
            parents_candidates.append({'parent1': parent1, 'parent2': parent2})
            member_counter += 2

        self.current_parents.append({'ranking': parents_candidates})
        # TODO: why where there three lists from ranking selection alone???

    def roulette_wheel_selection(self):  # probability-based
        """The conspicuous characteristic of this selection method is the fact that it gives to
        each member i of the current generation a probability p(i) of being selected,
        proportional to its fitness value f(i).

        Each member in the population occupies an area on the roulette wheel proportional to its
        fitness. Then, conceptually, the roulette wheel is spun as many times as the population size, each time
        selecting a member marked by the roulette-wheel pointer. Since the members are marked proportionally
        to their fitness, a member with a higher fitness is likely to receive more copies than a solution with a
        low fitness.

        For more details please refer to 'Introduction to Evolutionary Computing', sect. 5.2.3 'Implementing Selection
        Probabilities'. [DOI 10.1007/978-3-662-44874-8]"""
        fit_total = 0

        """In order to select members with regard to their fitness value compared to all of the values,
        we calculate the total sum of fitness values of all members in the current generation:"""
        for i in range(self.pop_size):
            fit_total += self.current_fitness_ranking[i].get('fitness value')

        """We use 'member_counter' as an index for the fitness ranking. While it's smaller than the elite
        size for the whole population, we simply copy-paste the old members into the new generation. That's why
        we automatically calculate it and focus on selecting pairs of members from the current generation as parents
        for crossover performed later. Only then will the 'elite' members be copy-pasted."""
        member_counter = 2 * self.elite_size

        """As every other one, this selection operator creates his own list of candidates for parents of the future
        generation from the current generation and appends it to the 'parents' field in this class:"""
        parents_candidates = []

        while member_counter < self.current_generation.size:
            """In each iteration we add two parents who will result in two children,
            which is why we use a while loop and 'jump' 2 population members in each iteration."""
            param = random.uniform(0, fit_total)
            fit_sum = 0
            index = 0

            while fit_sum < param and index < self.pop_size:
                fit_sum += self.current_fitness_ranking[index].get('fitness value')
                index += 1
            parent1 = self.current_generation.members[self.current_fitness_ranking[index].get('index')]

            param = random.uniform(0, fit_total)
            fit_sum = 0
            index = 0
            while fit_sum < param and index < self.pop_size:
                fit_sum += self.current_fitness_ranking[index].get('fitness value')
                index += 1
            parent2 = self.current_generation.members[self.current_fitness_ranking[index].get('index')]

            parents_candidates.append({'parent1': parent1, 'parent2': parent2})
            member_counter += 2

        self.current_parents.append({'roulette wheel': parents_candidates})

    def stochastic_universal_sampling(self):  # probability-based
        """It is an improved version of the roulette wheel selection operator, as described in 'Introduction to
        Evolutionary Computing' in sect. 5.2.3. We begin similarly to the roulette wheel, because we still base
        the probabilities of selection on the cumulative probability distribution, associated with the fitness values.
        """
        fit_total = 0
        cumulative_prob_distribution = []
        for i in range(self.pop_size):
            fit_total += self.current_fitness_ranking[i].get('fitness value')
            cumulative_prob_distribution.append(self.current_fitness_ranking[i].get('fitness value'))
        cumulative_prob_distribution = [fit / fit_total for fit in cumulative_prob_distribution]

        random_value = random.uniform(0, 1 / self.current_generation.size)
        parents = []
        index = 0
        member_counter = 2 * self.elite_size

        """As every other one, this selection operator creates his own list of candidates for parents of the future
        generation from the current generation and appends it to the 'parents' field in this class:"""
        parents_candidates = []

        # TODO: optimise loops; verify that it's correct

        while member_counter <= self.current_generation.size:
            while random_value <= cumulative_prob_distribution[index]:
                """We keep assigning given member as a new parent until the condition is met. This way we reflect
                the probability of it's selection."""
                new_parent = self.current_generation.members[self.current_fitness_ranking[index].get('index')]
                random_value += 1 / self.current_generation.size
                member_counter += 1
                parents.append(new_parent)
            index += 1

        """Now I rewrite parents into an organised list of pairs as dictionaries..."""
        index = 0
        while index < self.current_generation.size:
            parents_candidates.append({'parent1': parents[index], 'parent2': parents[index + 1]})
            index += 2

        """...and append it to the list of candidate parents lists:"""
        self.current_parents.append({'sus': parents_candidates})

    def perform_crossover(self, crossover_operator):
        children_candidates = []
        for parents_candidates in self.current_parents:
            list_of_parents_pairs = parents_candidates.values()
            for parents_pair in list_of_parents_pairs:
                children_candidates.append(
                    crossover_operator(
                        parents_pair[0].get('parent1'),
                        parents_pair[0].get('parent2')
                    )
                )
            self.current_children.append(
                {
                    'selection operator': parents_candidates.keys(),
                    'children': children_candidates
                }
            )

    def create_new_generation(self, selection_operator, crossover_operator):  # for single new generation creation
        """A method for combining selection and crossover operators over the current population to create a new one.
        For the moment we are assuming that there will be a single list of children candidates.
        Firstly we have to match the selection operator; then in each case we have to match the crossover operator:"""

        if selection_operator == 'sus':
            print('yes')

        match str(selection_operator):
            case 'ranking':
                self.ranking_selection()
                match crossover_operator:
                    case 'single point':
                        self.perform_crossover(crossover_operator=single_point_crossover)
                    case 'uniform':
                        self.perform_crossover(crossover_operator=uniform_crossover)
                    case 'plco':
                        self.perform_crossover(crossover_operator=plco)
            case 'roulette wheel':
                self.roulette_wheel_selection()
                match crossover_operator:
                    case 'single point':
                        self.perform_crossover(crossover_operator=single_point_crossover)
                    case 'uniform':
                        self.perform_crossover(crossover_operator=uniform_crossover)
                    case 'plco':
                        self.perform_crossover(crossover_operator=plco)
            case 'sus':  # abbreviation for stochastic universal sampling
                self.stochastic_universal_sampling()
                match crossover_operator:
                    case 'single point':
                        self.perform_crossover(crossover_operator=single_point_crossover)
                    case 'uniform':
                        self.perform_crossover(crossover_operator=uniform_crossover)
                    case 'plco':
                        self.perform_crossover(crossover_operator=plco)

        """Secondly, we create the new generation with children being a result od selection and crossover operators
        on the current population:"""
        new_generation = Generation(size=self.pop_size)

        for pair in self.current_children[0].get('children'):
            new_generation.add_member(genome=pair[0])
            new_generation.add_member(genome=pair[1])

        """Thirdly, we overwrite the current generation with the new one:"""
        self.current_generation = new_generation

    def mutate(self):
        """Mutation probability is the probability of 'resetting' a member of the current generation, i.e. changing
        it genome randomly. For optimisation purposes instead of a loop over the whole generation I calculate number
        of members to be mutated and then generate pseudo-randomly a list of member indexes in the current generation
        to be mutated."""
        number_of_mutations = floor(self.mutation_prob * self.current_generation.size)
        indexes = random.sample(range(self.current_generation.size), int(number_of_mutations))  # has to be an integer

        """For new (mutated) genome creation I use the generator passed to the superclass in it's initialisation:"""
        for index in indexes:
            self.current_generation.members[index].change_genes(
                self.current_generation.genome_generator(self.current_generation.genome_generator_args)
            )

    def reset_parents(self):
        self.current_parents = []

    def reset_children(self):
        self.current_children = []

    def change_population_size(self, pop_size):
        self.pop_size = pop_size