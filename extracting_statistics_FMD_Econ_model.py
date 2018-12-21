# extracting_statistics script #
# This script calculates several important statistics from the
# ag econ FMD model.  It reads exported files from the Vehicle
# Routing Problem (VRP) for the quarantine zone iterations.
#
# In order to create the VRPs for this script, first the
# script Iterative_Infection was run to create a series of five
# successive quarantine zone files as the infection progresses.
# Then the original VRP (found in the Random_Quarantine_Zones.mxd)
# was copied for each iteration. The quarantine zone files were
# added to the VRPs as polygon barriers. Each VRP was then improperly
# 'solved' to determine which locations were blocked by the barriers;
# this revealed the orders, depots and routes that were inaccessible.
# At this point, orders were exported as listed in `orders_list`.
# Then orders, routes and depots that were inaccessible were deleted
# from the iteration VRPs, and then they were properly solved.
# The orders and routes were exported, the orders being listed in
# `orders_solved_list`.

#
# SETUP
#
import os
import csv
import arcpy
import numpy as np
from Iterative_Infection import epidemic_curve

#
# PARAMETERS
#

csv_location = r'C:\Users\apddsouth\Documents\FMD_Truck_Econ_Paper\Results\results.csv'

orders_solved_no_quarantine = r'C:\Users\apddsouth\Documents\FMD_Truck_Econ_Paper\ArcMap_stuff\Quarantine_Iterations_a.gdb\no_quarantine_orders_solved'
orders_list = [
    r'C:\Users\apddsouth\Documents\FMD_Truck_Econ_Paper\ArcMap_stuff\Quarantine_Iterations_a.gdb\quarantine_zone_i0_orders',
    r'C:\Users\apddsouth\Documents\FMD_Truck_Econ_Paper\ArcMap_stuff\Quarantine_Iterations_a.gdb\quarantine_zone_i1_orders',
    r'C:\Users\apddsouth\Documents\FMD_Truck_Econ_Paper\ArcMap_stuff\Quarantine_Iterations_a.gdb\quarantine_zone_i2_orders',
    r'C:\Users\apddsouth\Documents\FMD_Truck_Econ_Paper\ArcMap_stuff\Quarantine_Iterations_a.gdb\quarantine_zone_i3_orders',
    r'C:\Users\apddsouth\Documents\FMD_Truck_Econ_Paper\ArcMap_stuff\Quarantine_Iterations_a.gdb\quarantine_zone_i4_orders',
    ]

orders_solved_list = [
    r'C:\Users\apddsouth\Documents\FMD_Truck_Econ_Paper\ArcMap_stuff\Quarantine_Iterations_a.gdb\quarantine_zone_i0_orders_solved',
    r'C:\Users\apddsouth\Documents\FMD_Truck_Econ_Paper\ArcMap_stuff\Quarantine_Iterations_a.gdb\quarantine_zone_i1_orders_solved',
    r'C:\Users\apddsouth\Documents\FMD_Truck_Econ_Paper\ArcMap_stuff\Quarantine_Iterations_a.gdb\quarantine_zone_i2_orders_solved',
    r'C:\Users\apddsouth\Documents\FMD_Truck_Econ_Paper\ArcMap_stuff\Quarantine_Iterations_a.gdb\quarantine_zone_i3_orders_solved',
    r'C:\Users\apddsouth\Documents\FMD_Truck_Econ_Paper\ArcMap_stuff\Quarantine_Iterations_a.gdb\quarantine_zone_i4_orders_solved',
    ]

routes_solved_no_quarantine = r'C:\Users\apddsouth\Documents\FMD_Truck_Econ_Paper\ArcMap_stuff\Quarantine_Iterations_a.gdb\no_quarantine_routes_solved'
routes_solved_list = [
    r'C:\Users\apddsouth\Documents\FMD_Truck_Econ_Paper\ArcMap_stuff\Quarantine_Iterations_a.gdb\quarantine_zone_i0_routes_solved',
    r'C:\Users\apddsouth\Documents\FMD_Truck_Econ_Paper\ArcMap_stuff\Quarantine_Iterations_a.gdb\quarantine_zone_i1_routes_solved',
    r'C:\Users\apddsouth\Documents\FMD_Truck_Econ_Paper\ArcMap_stuff\Quarantine_Iterations_a.gdb\quarantine_zone_i2_routes_solved',
    r'C:\Users\apddsouth\Documents\FMD_Truck_Econ_Paper\ArcMap_stuff\Quarantine_Iterations_a.gdb\quarantine_zone_i3_routes_solved',
    r'C:\Users\apddsouth\Documents\FMD_Truck_Econ_Paper\ArcMap_stuff\Quarantine_Iterations_a.gdb\quarantine_zone_i4_routes_solved',
    ]

#
# DEFINE FUNCTIONS
#
def total_milk_at_each_creamery(orders_solved):
    # Create a bunch of lists within a list, one for each Depot.
    milk_list = [[] for thing in range (0,16)]
    with arcpy.da.SearchCursor(orders_solved, ['PickupQuantities', 'RouteName']) as search_cursor:
        for row in search_cursor:
            route_name = row[1]
            if route_name is not None:
                # Since the depot name is saved as part of the name of the route, we can use that.
                # We know it will be after the index 6 and before the second underscore.
                second_underscore = int(route_name.find('_', route_name.find('_') + 1))
                depot_name = int(route_name[6:second_underscore])

                # Now add the PickupQuantities value to the proper sublist.
                milk_list[depot_name] += [int(row[0])]

    # Now convert each sublist to a total for that sublist. We don't need the individual info.
    for index in range(0, len(milk_list)):
        milk_list[index] = sum(milk_list[index])
    return milk_list


def find_average_route_distance_per_creamery(routes_solved, whole_model_average=False):
    # Create a lists of lists, with one sublist for each Depot.
    route_list = [ [] for thing in range(0, 16)]
    with arcpy.da.SearchCursor(routes_solved, ['StartDepotName', 'OrderCount', 'TotalDistance']) as search_cursor:
        for row in search_cursor:
            # If the route picked up milk at at least one place:
            if row[1] is not None:
                # Save the distance (in meters) it to `route_list` for the corresponding depot.
                route_list[int(row[0])] += [int(row[2])]

    if not whole_model_average:
        # Now convert each sublist to a route average for that sublist. We don't need the individual info.
        for index in range(0, len(route_list)):
            if not len(route_list[index]) == 0:
                route_list[index] = int(round(
                                              np.average(route_list[index])))
            else:
                route_list[index] = 0
    elif whole_model_average:
        temp_list = []
        if not len(route_list) == 0:
            for sublist in route_list:
                for item in sublist:
                    temp_list += [item]
        route_list = [int(round(np.average(temp_list)))]
    return route_list


def find_unsatisfied_milk(orders_file):
    # Define milk_list, which will be used to store each instance of unsatisfied milk.
    milk_list = []

    # Search through orders_file and store all unsatisfied milk.
    with arcpy.da.SearchCursor(orders_file, ['PickupQuantities', 'Status']) as search_cursor:
        for row in search_cursor:
            # If the order wasn't completed, save the PickupQuantities value.
            # Status=0 means no violations, Status=6 means time window violation
            # which doesn't matter.
            if not row[1] in (0, 6):
                milk_list += [int(row[0])]

    return sum(milk_list)


def write_to_CSV(CSV, iteration, orders, orders_solved, routes_solved, new_CSV=False):
    if new_CSV:
        # First, clear the CSV of anything that it contained before, or create it
        # if it didn't previously exist.
        open(CSV, 'wb')

        # Now write the first row with the field labels.
        with open(CSV, 'ab') as g:
            writer = csv.writer(g, dialect='excel')
            writer.writerow(['iteration',] +
                            ['c' + str(x) for x in range(0, 16)] +
                            ['c' + str(y) + '_av_dist' for y in range(0, 16)] +
                            ['Unsatisfied milk in quarantine zones',
                             'Unsatisfied milk indirectly caused by quarantine',
                             'Whole_model_av_distance'])

    # Collect values for the milk collected at each creamery during this period.
    milk_at_creameries = total_milk_at_each_creamery(orders_solved)
    av_route_dist = find_average_route_distance_per_creamery(routes_solved)
    av_route_dist_whole_model = find_average_route_distance_per_creamery(routes_solved, whole_model_average=True)

    # Write a new line in the CSV
    with open(CSV, 'ab') as g:
        writer = csv.writer(g, dialect='excel')
        writer.writerow([iteration] +
                        milk_at_creameries +
                        av_route_dist +
                        [find_unsatisfied_milk(orders), find_unsatisfied_milk(orders_solved)] +
                        av_route_dist_whole_model)

    return None


#
# DO STUFF
#
if __name__ == '__main__':
    print "Script starting..."
    # Loop for each iteration of the quarantine zones, as the epidemic gets worse.
    for iteration in range(-1, len(epidemic_curve)):
        print "Iteration:", iteration
        # For the uninfected iteration, just use `orders_solved_no_quarantine`.
        if iteration == -1:
            orders_file = orders_solved_no_quarantine
            orders_solved_file = orders_solved_no_quarantine
            routes_solved_file = routes_solved_no_quarantine
            write_to_CSV(csv_location, iteration, orders_file,
                         orders_solved_file, routes_solved_file, new_CSV=True)
        else:
            orders_file = orders_list[iteration]
            orders_solved_file = orders_solved_list[iteration]
            routes_solved_file = routes_solved_list[iteration]
            write_to_CSV(csv_location, iteration, orders_file,
                         orders_solved_file, routes_solved_file)

    print "Script completed! H*ck yes. Sorry for cursing. I am excite."
