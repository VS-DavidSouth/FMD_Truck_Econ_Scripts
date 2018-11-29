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

def read_CSVs():
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
    # the currently_infected_farms array.
    FLAPS_array = []
    with open(FLAPS) as FLAPS_CSV:
        reader = csv.reader(FLAPS_CSV, delimiter=',')
        for row in reader:
            if not row[0] == 'Unit ID':
                FLAPS_array.append(row)
    FLAPS_array = np.array(FLAPS_array)

    return epidemic_curve, FLAPS_array

epidemic_curve, FLAPS_array = read_CSVs()


def create_quarantine_zone(output_path, current_iteration, previously_infected_farms, selection_type='random', random_seed=None):
    """
    Set selection_type='random' for equal probability of any point being selected, and selection_type='dw'
    or selection_type='distance_weighted' for selecting points randomly weighted by distance.
    :param input_point_data: The file path to the point shapefile or feature class with the farms to be infected.
    :param current_iteration: The current step of the progression through the epidemic curve.
    :return:
    """

    previously_infected_farms = np.array(previously_infected_farms)

    # Create a list of all farms that were not infected in the previous iteration.
    uninfected_farms = []
    for farm in FLAPS_array:
        if farm[0] not in previously_infected_farms[:0]:
            uninfected_farms.append(farm)
    uninfected_farms = np.array(uninfected_farms)
    print("Uninfected farms: " + str(len(uninfected_farms)))

    def buffer(farms_to_quarantine, output_file_path, buffer_dist=7):

        # Create blank table based on FLAPS. Use 'in_memory' once you are done testing.
        temp_location = r'C:\Users\apddsouth\Documents\FMD_Truck_Econ_Paper\ArcMap_stuff\Test_GDB.gdb'
        temp_name = 'temp_table'
        temp_table = os.path.join(temp_location, temp_name)
        if arcpy.Exists(temp_table):
            arcpy.Delete_management(temp_table)
        arcpy.CreateTable_management(temp_location, temp_name, FLAPS)

        # Fill table with the infected FLAPS points.
        fields = ['Unit ID', 'Production Type', 'Cattle', 'Goats', 'Sheep', 'Swine',
                  'X coordinate', 'Y coordinate', 'FIPS', 'State', 'Latitude', 'Longitude',]
        with arcpy.da.InsertCursor(temp_table, fields) as cursor:
            for farm in FLAPS_array[0]:
                if farm[0] in farms_to_quarantine[:0]:
                    cursor.insertRow(farm)

        # Make a point feature class out of the table.
        x_coords = "Longitude"
        y_coords = "Latitude"
        arcpy.management.XYTableToPoint(temp_table, temp_table+'_fc',
                                x_coords, y_coords)

        # Buffer the feature class.
        print("Buffering for iteration " + str(current_iteration))
        arcpy.Buffer_analysis(in_features=input_points,
                              out_feature_class=output_file_path,
                              buffer_distance_or_field="%s Kilometers" %str(buffer_dist),
                              line_side="FULL", line_end_type="ROUND",
                              dissolve_option="ALL", dissolve_field="", method="PLANAR")

        # Delete the table and the feature class.
        arcpy.Delete_management([temp_table, temp_table+'_fc'])




    def select_random_distance_weighted():
        return selected_points

    def infection_spreads():
        # Set up for random seeding in case we want to make the results repeatable.
        if random_seed is not None:
            random.seed(random_seed)

        if selection_type == 'random':
            # Randomly sample (without replacement) a number of uninfected farms equal to the current
            # number of farms that should be infected at this stage of the epidemic curve.
            print "uninfected_farms:" + str(len(uninfected_farms)) # REMOVE THIS LATER
            print uninfected_farms[0:5, 0]
            print "farms to infect: " + str(epidemic_curve[current_iteration,0])
            newly_infected_farms = random.sample(uninfected_farms, int(epidemic_curve[current_iteration,0]))
            print "newly infected farms: ", len(newly_infected_farms)
            print "previously infected farms:", previously_infected_farms

            # Make an array of all the infected farms
            if previously_infected_farms.size == 0:
                currently_infected_farms = newly_infected_farms
            else:
                currently_infected_farms = np.concatenate( (previously_infected_farms, newly_infected_farms), axis=1 )

            buffer(currently_infected_farms, output_path)

            return currently_infected_farms

        elif selection_type=='dw' or selection_type=='distance_weighted':
            buffer(select_random_distance_weighted(), output_path)


    return infection_spreads()

def clear_GDB(GDB):
    walk = arcpy.da.Walk(GDB)
    for dirpath, dirnames, filenames in walk:
        for filename in filenames:
            arcpy.Delete_management(os.path.join(dirpath, filename))

if __name__ == '__main__':
    print("Script starting...")
    previously_infected_farms = np.array([[]])
    num_iterations = len(epidemic_curve)

    # Go through output_folder and delete anything with 'quarantine_zone' in its name so that there aren't
    # a whole bunch of old files floating around.
    walk = arcpy.da.Walk(output_GDB)
    for dirpath, dirnames, filenames in walk:
        for filename in filenames:
            if 'quarantine_zone' in filename:
                arcpy.Delete_management(os.path.join(dirpath, filename))

    for current_iteration in range (0, num_iterations):
        output_file = os.path.join(output_GDB, 'quarantine_zone_i' + str(current_iteration))

        # Create the quarantine buffer zone for this iteration, and save which farms are infected as
        # the previously_infected_farms variable, so you can use it for the next iteration.
        previously_infected_farms = create_quarantine_zone(output_file, current_iteration, previously_infected_farms)

    print ("~~~~~~~Script Completed!~~~~~~~")
