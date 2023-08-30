import os
import json
from itertools import combinations
import itertools
import time
import math
import csv
import random

def get_orders(target_path):
    orders = []
    for filename in os.listdir(target_path):
        file_path = os.path.join(target_path, filename)
        if os.path.isfile(file_path):
            with open(file_path, "r") as file:
                content = file.read()
                parsed = json.loads(content)
                order = parsed["testOrder"]
                orders.append(order)
    return orders

def get_seq(order, t):
    return list(combinations(order, t))

def count_unique_seq(order_list, t):
    seq_list = [get_seq(order, t) for order in order_list]

    unique_subsequences = set(seq for sublist in seq_list for seq in sublist)

    return len(unique_subsequences)


def max_cover_order(orders, selected_orders, t):
    max_cover = 0
    max_order = None
    for order in orders:
        if order not in selected_orders:
            temp_orders = selected_orders + [order]
            temp_cover = count_unique_seq(temp_orders, t)
            cover = count_unique_seq(selected_orders + [order], t)
            #print(f"Temp coverage after adding {order}: {temp_cover}")
            #print(f"Cover after adding {order}: {cover}")
            if cover > max_cover:
                max_cover = cover
                max_order = order
    return max_order


def sort_orders(orders, t):
    print(len(orders))
    total_possibilities = math.factorial(len(orders[0])) / math.factorial(len(orders[0]) - t) # total possibilities

    sorted_orders = []
    while orders:
        current_batch = [orders[0]]  # start with the first order
        orders.remove(orders[0])
        coverage = min(count_unique_seq(current_batch, t) / total_possibilities * 100, 100)
        while coverage < 100 and orders:
            next_order = max_cover_order(orders, current_batch, t)
            current_batch.append(next_order)
            orders.remove(next_order)
            coverage = min(count_unique_seq(current_batch, t) / total_possibilities * 100, 100)
        print(f"Batch with {len(current_batch)} orders reached {coverage:.2f}% coverage")
        sorted_orders.extend(current_batch)

    return sorted_orders

def get_victims_or_brittle(github_slug, module, target_path_polluter_cleaner):
    output = {}
    unique_victims_brittle = set()

    with open(target_path_polluter_cleaner, 'r') as file:
        reader = csv.DictReader(file)
        index = 0
        for row in reader:
            module_name = row['module'].split('/')[-1] if row['module'] != '.' else ''
            if row['github_slug'] == github_slug and module_name == module:
                if row['type_victim_or_brittle'] == 'victim':
                    if row['potential_cleaner'] == row['polluter/state-setter']:
                        output[index] = [row['polluter/state-setter'], row['victim/brittle'], 3]
                        unique_victims_brittle.add(row['victim/brittle'])
                        index += 1

                        output[index] = [row['victim/brittle'], row['polluter/state-setter'], 4]
                        unique_victims_brittle.add(row['victim/brittle'])
                        index += 1
                    elif row['potential_cleaner']:
                        output[index] = [row['polluter/state-setter'], row['victim/brittle'], row['potential_cleaner'], 1]
                        unique_victims_brittle.add(row['victim/brittle'])
                        index += 1

                        output[index] = [row['polluter/state-setter'], row['potential_cleaner'], row['victim/brittle'], 2]
                        unique_victims_brittle.add(row['victim/brittle'])
                        index += 1
                    else:
                        output[index] = [row['polluter/state-setter'], row['victim/brittle'], 3]
                        unique_victims_brittle.add(row['victim/brittle'])
                        index += 1

                        output[index] = [row['victim/brittle'], row['polluter/state-setter'], 4]
                        unique_victims_brittle.add(row['victim/brittle'])
                        index += 1
                elif row['type_victim_or_brittle'] == 'brittle':
                    output[index] = [row['polluter/state-setter'], row['victim/brittle'], 3]
                    unique_victims_brittle.add(row['victim/brittle'])
                    index += 1

                    output[index] = [row['victim/brittle'], row['polluter/state-setter'], 4]
                    unique_victims_brittle.add(row['victim/brittle'])
                    index += 1

    unique_victims_brittle_list = list(unique_victims_brittle)
    return output, unique_victims_brittle_list



def find_OD_in_sorted_orders(sorted_orders, OD_dict, unique_od_test_list):
    OD_found = set()
    sorted_order_count = 0

    for order in sorted_orders:
        sorted_order_count += 1
        keys_to_remove = []

        for key, OD in OD_dict.items():
            if all(elem in order for elem in OD[:-1]) and all(order.index(OD[j]) <= order.index(OD[j + 1]) for j in range(len(OD) - 2)):
                OD_found.add(tuple(OD))
                last_element = OD[-1]
                if last_element == 1 and OD[1] in unique_od_test_list:
                    if key+1 in OD_dict:
                        keys_to_remove.append(key)
                    else:
                        unique_od_test_list.remove(OD[1])
                        #keys_to_remove.extend([k for k, od in OD_dict.items() if od[1] == OD[1] or od[2] == OD[1]])
                elif last_element == 2 and OD[2] in unique_od_test_list:
                    if key-1 in OD_dict:
                        keys_to_remove.append(key)
                    else:
                        unique_od_test_list.remove(OD[2])
                        #keys_to_remove.extend([k for k, od in OD_dict.items() if od[1] == OD[2] or od[2] == OD[2]])


                elif last_element == 3 and OD[1] in unique_od_test_list:
                    if key+1 in OD_dict:
                        keys_to_remove.append(key)
                    else:
                        unique_od_test_list.remove(OD[1])
                        #keys_to_remove.extend([k for k, od in OD_dict.items() if od[1] == OD[1] or od[0] == OD[1]])

                elif last_element == 4 and OD[0] in unique_od_test_list:
                    if key-1 in OD_dict:
                        keys_to_remove.append(key)
                    else:
                        unique_od_test_list.remove(OD[0])
                        #keys_to_remove.extend([k for k, od in OD_dict.items() if od[1] == OD[0] or od[0] == OD[0]])

        for key in keys_to_remove:
            OD_dict.pop(key, None)

        if len(unique_od_test_list) == 0:
            return sorted_order_count, OD_found, OD_dict
    if len(unique_od_test_list) != 0:
        print(unique_od_test_list)
    return sorted_order_count, OD_found, OD_dict


def count_ODs_in_order(order, OD_dict):
    # Create a flag 2D array
    flag_2D_array = set()

    for OD in OD_dict.values():
        # Check if all elements of OD (except the last one) are in order and in the same sequence
        if all(elem in order for elem in OD[:-1]) and all(order.index(OD[j]) <= order.index(OD[j + 1]) for j in range(len(OD) - 2)):
            last_element = OD[-1]
            if last_element == 1:
                flag_2D_array.add((last_element, OD[1]))
            elif last_element == 2:
                flag_2D_array.add((last_element, OD[2]))
            elif last_element == 3:
                flag_2D_array.add((last_element, OD[1]))
            elif last_element == 4:
                flag_2D_array.add((last_element, OD[0]))

    print(f"unique found: {len(flag_2D_array)}")
    return len(flag_2D_array)

def find_OD_in_sorted_orders_greedy(sorted_orders, OD_dict, unique_od_test_list):
    #print(sorted_orders)
    #print(OD_dict)
    print(unique_od_test_list)
    # Sorting the orders based on the number of ODs found in each order
    sorted_orders = sorted(sorted_orders, key=lambda order: count_ODs_in_order(order, OD_dict), reverse=True)
    #print(sorted_orders)
    return find_OD_in_sorted_orders(sorted_orders,OD_dict,unique_od_test_list)

def clear_file(file_path):
    with open(file_path, "w") as f:
        pass

def remove_last_line(file_path):
    with open(file_path, "r") as file:
        lines = file.readlines()

    if lines:
        lines.pop()

    with open(file_path, "w") as file:
        file.writelines(lines)

def write_indices_to_file(n, indices, output_file):
    with open(output_file, "a") as f:
        index_list = [str(index) for index in indices]
        f.write(str(n) + ", " + " ".join(index_list) + "\n")

def genRandomBoxes(nvars, size, number):
    res = {}
    if math.factorial(nvars) / math.factorial(nvars - size) < number:
        print('There are only ' + str(math.factorial(nvars) / math.factorial(nvars - size)) + ' permutations')
        for comb in itertools.permutations(range(1, nvars + 1), size):
            res[comb] = 0
        return res
    for i in range(number):
        res[tuple(random.sample(range(1, nvars + 1), size))] = 0
    return res

def approximate_permutation(samplefile, size, epsilon, delta):
    nBoxes = math.ceil(3 * math.log(2 / delta) / (epsilon*epsilon))
    with open(samplefile, "r") as f:
        nvars = len(f.readline().strip().split(',')[1].strip().split(' '))
    boxes = genRandomBoxes(nvars, size, nBoxes)
    with open(samplefile, "r") as f:
        for line in f:
            s = list(map(int, line.strip().split(',')[1].strip().split(' ')))
            for perm in boxes.keys():
                if boxes[perm] == 0 and all(s[abs(perm[i])-1] == perm[i] for i in range(size)):
                    boxes[perm] = 1
    coveredBoxes = sum(boxes.values())
    countRes = int((math.factorial(nvars) / math.factorial(nvars - size)) * coveredBoxes / nBoxes)
    print("Approximate number of permutations " + str(countRes))
    return countRes

def create_test_order_mapping(target_path):
    test_order_mapping = {}
    index = 1
    for path in os.listdir(target_path):
        file = os.path.join(target_path, path)
        with open(file, "r") as f:
            data = json.load(f)
            test_orders = data['testOrder']
            for test_order in test_orders:
                if test_order not in test_order_mapping:
                    test_order_mapping[test_order] = index 
                    index += 1
    return test_order_mapping

def sort_orders_approxcov(target_path, orders, t, output_file):
    sorted = []
    clear_file(output_file)
    #first_round = os.path.join(target_path, os.listdir(target_path)[0])
    test_order_mapping = create_test_order_mapping(target_path)
    line = 1 
    while orders:
        max_order = []
        max_score = -1
        for order in orders:
            new_indices = [test_order_mapping[test_order] for test_order in order]
            write_indices_to_file(line, new_indices, output_file)
            score = approximate_permutation(output_file, t, 0.1, 0.1)
            if score > max_score:
                max_order = order
                max_score = score
            remove_last_line(output_file)
        if max_order in orders:
            orders.remove(max_order)
        sorted.append(max_order)
        new_indices = [test_order_mapping[test_order] for test_order in max_order]
        write_indices_to_file(line, new_indices, output_file)
        line += 1
    return sorted

if __name__ == "__main__":
    # github_slug = input("Enter the github slug: ")
    # module = input("Enter the module name (or press Enter to match any): ")
    # target_path_polluter_cleaner = input("Please enter the target path for polluter cleaner list: ")
    # result,unique_od_test_list = get_victims_or_brittle(github_slug, module,target_path_polluter_cleaner)
    # print(f"Number pairs found: {len(result)}")
    # print(f"Number of OD tests found: {len(unique_od_test_list)}")
    # target_path = input("Please enter the target path for generated orders: ")
    # orders = get_orders(target_path)
    # t = int(input("Please enter the value of t: "))
    # #order_count, OD_found, not_found_ODs = find_OD_in_sorted_orders(orders, result,unique_od_test_list)
    # #print(f"Number of needed order: {order_count}")
    # #print("Sorted Orders: ")


    # num_shuffle_iterations = 1000
    # total_rank_point=0
    # total_rank_point_greedy=0
    # for i in range(num_shuffle_iterations):
    #     shuffled_orders = orders.copy()  # Create a copy of the original orders
    #     copy_of_results = result.copy()
    #     copy_of_unique_od_test_list = unique_od_test_list.copy()
    #     random_seed = i  # Use the iteration index as the random seed
    #     random.seed(random_seed)
    #     random.shuffle(shuffled_orders)
    #     order_count, OD_found, not_found_ODs = find_OD_in_sorted_orders(shuffled_orders, copy_of_results, copy_of_unique_od_test_list)
    #     print(order_count)
    #     total_rank_point=total_rank_point+order_count

    #     #sorted_order_count_greedy, OD_found_greedy, not_found_ODs_greedy= find_OD_in_sorted_orders_greedy(shuffled_orders, result)
    #     #print(f"Number of avg orders needed to find all OD from greedy: {sorted_order_count_greedy}")
    #     #total_rank_point_greedy=total_rank_point_greedy+sorted_order_count_greedy
    #     #print("Shuffle", i + 1, ":", shuffled_orders)

    # print(f"Number of avg orders needed to find all OD from random seed: {total_rank_point/num_shuffle_iterations}")
    # #print(f"Number of avg orders needed to find all OD from random seed greedy: {total_rank_point_greedy/num_shuffle_iterations}")
    # sorted_orders = sort_orders(orders, t)
    # copy_of_results_sorted = result.copy()
    # copy_of_unique_od_test_list_sorted = unique_od_test_list.copy()
    # sorted_order_count, OD_found, not_found_ODs = find_OD_in_sorted_orders(sorted_orders, copy_of_results_sorted ,copy_of_unique_od_test_list_sorted)
    # print(f"Number of sorted orders needed to find all OD: {sorted_order_count}")
    # #print("OD found: ", OD_found)
    # #print("OD not found: ", not_found_ODs)
    # orders_greedy = orders.copy()  # Create a copy of the original orders
    # results_greedy = result.copy()
    # unique_od_test_list_greedy=unique_od_test_list.copy()
    # #sorted_order_count_greedy, OD_found_greedy, not_found_ODs_greedy= find_OD_in_sorted_orders_greedy(orders_greedy , results_greedy ,unique_od_test_list_greedy)
    # #print(f"Number of orders needed to find all OD in greedy: {sorted_order_count_greedy}")

    # target_path = input("Please enter the target path for generated orders: ")
    # orders = get_orders(target_path)
    # t = int(input("Please enter the value of t: "))
    # start = time.time()
    # sorted_orders = sort_orders(orders, t)
    # end = time.time()
    # print("Time to sort orders: " + str(end - start))
    # #target_path = input("Please enter the target path for generated orders: ")
    # output_file = input("Please enter the output file path: ")
    # clear_file(output_file)
    # #orders = get_orders(target_path)
    # #t = int(input("Please enter the value of t: "))
    # first_round = os.path.join(target_path, os.listdir(target_path)[0])
    # test_order_mapping = create_test_order_mapping(first_round)
    # indices = test_order_mapping.values()
    # write_indices_to_file(1, indices, output_file)
    # for i in range(len(orders)):
    #     if i == 0:
    #         pass
    #     else:
    #         test_orders = orders[i]
    #         new_indices = [test_order_mapping[test_order] - 1 for test_order in test_orders]
    #         write_indices_to_file(i + 1, new_indices, output_file)
    # start = time.time()
    # approximate_permutation(output_file, t, 0.1, 0.1)
    # end = time.time()
    # print("Time to check coverage: " + str(end - start))

    #target_path = input("Please enter the target path for generated orders: ")
    target_path = "/Users/satvikeltepu/Desktop/GenerateOrders/generate_orders_java/outputs/inter/Activiti/Activiti/activiti-spring-boot-starter/b11f757"
    output_file = "/Users/satvikeltepu/Desktop/GenerateOrders/generate_orders_java/output.txt"
    orders = get_orders(target_path)
    manual_orders = orders.copy()
    sorted_orders = sort_orders(manual_orders, 2)
    approxcov_orders = orders.copy()
    start = time.time()
    sorted_approxcov = sort_orders_approxcov(target_path, approxcov_orders, 2, output_file)
    print(sorted_orders == sorted_approxcov)
    end = time.time()
    print("Number of Orders: " + str(len(orders)))
    print("Time elapsed: " + str(end-start))