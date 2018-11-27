# This script was designed to create a series of quarantine zones based on random points,
# simulating an infection curve.

import os
import csv
import arcpy
import random
import numpy as np


epidemic_curve_CSV = r'C:\Users\apddsouth\Documents\FMD_Truck_Econ_Paper\Stuff_sent_by_Amy\Epi_Curve.csv'
FLAPS = r'C:\Users\apddsouth\Documents\FMD_Truck_Econ_Paper\Source_Data\FLAPS_National_Farm_File_MI.csv'
output_GDB = r'C:\Users\apddsouth\Documents\FMD_Truck_Econ_Paper\ArcMap_stuff\Quarantine_Iterations.gdb'

# Generate a numpy array based on epidemic_curve_CSV.
# This needs to be tailored if the CSV is replaced or altered!
epidemic_curve = []
with open(epidemic_curve_CSV) as csv_file:
    reader = csv.reader(csv_file, delimiter=',')
    for row in reader:
        if not row[0] == 'First day of the week':
            epidemic_curve.append(row[1:])
epidemic_curve = np.array(epidemic_curve)

# Generate a numpy array from FLAPS. This will be used to add to and remove from
# currently_infected_farms.
all_FLAPS = []
with open(FLAPS) as FLAPS_CSV:
    reader = csv.reader(FLAPS_CSV, delimiter=',')
    for row in reader:
        if not row[0] = 'Unit ID':
            all_FLAPS.append(row)
all_FLAPS = np.array(all_FLAPS)

def create_quarantine_zone(output_path, current_iteration, previously_infected_farms, selection_type='random', random_seed=None):
    """
    Set selection_type='random' for equal probability of any point being selected, and selection_type='dw'
    or selection_type='distance_weighted' for selecting points randomly weighted by distance.
    :param input_point_data: The file path to the point shapefile or feature class with the farms to be infected.
    :param current_iteration: The current step of the progression through the epidemic curve.
    :return:
    """

    # Create a list of all farms that were not infected in the previous iteration.
    uninfected_farms = []
    for farm in all_FLAPS[0]:
        if farm[0] not in previously_infected_farms:
            uninfected_farms.append(farm)


    def buffer(input_points, output_file_path, buffer_dist=7):

        arcpy.Buffer_analysis(in_features=input_points,
                              out_feature_class=output_file_path,
                              buffer_distance_or_field="%s Kilometers" %str(buffer_dist),
                              line_side="FULL", line_end_type="ROUND",
                              dissolve_option="ALL", dissolve_field="", method="PLANAR")


    def select_random_distance_weighted():
        return selected_points

    def infection_spreads():

        # Set up for random seeding in case we want to make the results repeatable.
        if random_seed is not None:
            random.seed(random_seed)

        if selection_type=='random':
            # Randomly sample (without replacement) a number of uninfected farms equal to the current
            # number of farms that should be infected at this stage of the epidemic curve.
            newly_infected_farms = random.sample(uninfected_farms, epidemic_curve[current_iteration,0])

            # Make an array of all the infected farms
            currently_infected_farms = np.concatenate( (previously_infected_farms, newly_infected_farms), axis=1 )

            buffer(currently_infected_farms, output_path)

            return currently_infected_farms

        elif selection_type=='dw' or selection_type=='distance_weighted':
            buffer(select_random_distance_weighted(), output_path)


    return infection_spreads()

if __name__ == '__main__':
    previously_infected_farms = []
    num_iterations = len(epidemic_curve)

    # Go through output_folder and delete anything with 'quarantine_zone' in its name so that there aren't
    # a whole bunch of old files floating around.
    walk = arcpy.da.Walk(cluster_GDB, type="Point")
    for dirpath, dirnames, filenames in walk:
        for filename in filenames:
            if 'quarantine_zone' in filename:
                arcpy.Delete_management(os.path.join(dirpath, filename))

    for current_iteration in range (1, num_iterations+1):
        output_file = os.path.join(output_GDB, 'quarantine_zone_i' + str(current_iteration))

        # Create the quarantine buffer zone for this iteration, and save which farms are infected as
        # the previously_infected_farms variable, so you can use it for the next iteration.
        previously_infected_farms = create_quarantine_zone(output_file, current_iteration, previously_infected_farms)