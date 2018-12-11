# This script was designed to create a series of quarantine zones based on random points,
# simulating an infection curve.

import os
import csv
import arcpy
import numpy as np

FLAPS = r'C:\Users\apddsouth\Documents\FMD_Truck_Econ_Paper\Source_Data\FLAPS_National_Farm_File_MI.csv'
output_GDB = r'C:\Users\apddsouth\Documents\FMD_Truck_Econ_Paper\ArcMap_stuff\Quarantine_Iterations.gdb'

# The source for the following epidemic curve data are from thsi: r'C:\Users\apddsouth\Documents\FMD_Truck_Econ_Paper\Stuff_sent_by_Amy\Epi_Curve.csv'
# Note that these data were originally in a per-week format, but they have been combined to a bi-weekly format.
# The date in the annotation is the first day of the corresponding weeks of the UK FMD outbreak.
epidemic_curve = np.array([
    7 + 62,       # 2/20/2001 and 2/27/2001
    104 + 153,    # 3/6/2001 and 3/13/2001
    289 + 299,    # 3/20/2001 and 3/30/2001
    221 + 190,    # 4/3/2001 and 4/10/2001
    110 + 77, ])  # 4/17/2001 and 4/24/2001


def read_CSV():

    # The following code is left in case we do want to try to do structured arrays.
    #epidemic_curve = np.array(epidemic_curve, dtype={'names':('New Cases', 'Cumulative Cases'),
    #                                                 'formats': ('u2', 'u2')})
                                                    # See FLAPS_array section below to verify format types.
    #epidemic_curve = np.array(epidemic_curve, dtype=[('New Cases', 'i4'), ('Cumulative Cases', 'i4')])

    # Generate a numpy array from FLAPS. This will be used to add to and remove from
    # the currently_infected_farms array.
    FLAPS_array = []
    with open(FLAPS) as FLAPS_CSV:
        FLAPS_reader = csv.reader(FLAPS_CSV, delimiter=',')
        for row in FLAPS_reader:
            if not row[0] == 'Unit ID':
                FLAPS_array.append(row)
    FLAPS_array = np.array(FLAPS_array)
                           #dtype={'names':('Unit ID', 'Production Type', 'Cattle', 'Goats',      # These were commented out because for some reason
                           #                    'Sheep', 'Swine', 'X coordinate', 'Y coordinate',   # assigning names caused the numbers to change.
                           #                    'FIPS', 'State', 'Latitude', 'Longitude'),
                           #       'formats':('u4', 'U30', 'u2', 'u2',
                           #                  'u2', 'u2', 'u4', 'u4',
                           #                  'u2', 'U5', 'f8', 'f8')})
                                           # To double check the types, feel free to look here:
                                           # https://docs.scipy.org/doc/numpy-1.15.1/reference/arrays.dtypes.html'
                                           # 'u4' - 32-bit unsigned integer, 'U30' - Unicode string with 30- characters,
                                           # 'u2' - 16-bit unsigned integer, 'f8' - 64-bit floating-point number



    return FLAPS_array

FLAPS_array = read_CSV()

def clear_GDB(GDB):     # THIS MAY DELETE THE GDB ITSELF. NEED TO CHECK ON THIS FUNCTION.
    walk = arcpy.da.Walk(GDB)
    for dirpath, dirnames, filenames in walk:
        for filename in filenames:
            arcpy.Delete_management(os.path.join(dirpath, filename))

def create_quarantine_zone(output_GDB, current_iteration, previously_infected_farms,
                           selection_type='random', random_seed=None):

    # Set selection_type='random' for equal probability of any point being selected, and selection_type='dw'
    # or selection_type='distance_weighted' for selecting points randomly weighted by distance.

    clear_GDB(output_GDB)

    previously_infected_farms = np.array(previously_infected_farms)

    # Create a list of all farms that were not infected in the previous iteration.
    uninfected_farms = []
    for farm in FLAPS_array:
        # If previously_infected_farms is empty (meaning this is the first iteration),
        # then just add everything to the uninfected list.
        if previously_infected_farms.size == 0:
            uninfected_farms.append(farm)
        # Otherwise, add only the places that aren't in the previously_infected_farms array.
        elif farm[0] not in previously_infected_farms[:,0]:
            uninfected_farms.append(farm)
    uninfected_farms = np.array(uninfected_farms)
    print("Uninfected farms: " + str(len(uninfected_farms)))

    # Now do the same process, but only collect the dairies. This will be used to sample the primary (original)
    # infected farm that infects all the others.
    dairies = []
    for farm in FLAPS_array:
        if farm[1] == 'dairy_l' or farm[1] == 'dairy_s':
            dairies.append(farm)
    dairies = np.array(dairies)

    def buffer_infected_farms(farms_to_quarantine, buffer_dist=7):

        # Create blank table based on FLAPS. Use 'in_memory' once you are done testing.
        temp_location = r'C:\Users\apddsouth\Documents\FMD_Truck_Econ_Paper\ArcMap_stuff'
        temp_name = 'temp_CSV_i' + str(current_iteration) + '.csv'
        temp_fc = os.path.join(temp_location, 'temp_fc_i' + str(current_iteration))
        temp_fc_points = os.path.join(temp_location, 'Test_GDB.gdb', 'temp_fc_i' + str(current_iteration) + '_points')

        open(os.path.join(temp_location, temp_name), 'wb')
        with open(os.path.join(temp_location, temp_name), 'ab') as g:
            writer = csv.writer(g, dialect='excel')

            # Fill table with the infected FLAPS points.
            fields = ['Unit ID', 'Production Type', 'Cattle', 'Goats', 'Sheep', 'Swine',
                      'X coordinate', 'Y coordinate', 'FIPS', 'State', 'Latitude', 'Longitude',]
            writer.writerow(fields)

            for farm in FLAPS_array:
                if farm[0] in farms_to_quarantine[:,0]:
                    writer.writerow(farm)

        if arcpy.Exists(temp_fc):
            arcpy.Delete_management(temp_fc)
        if arcpy.Exists(temp_fc_points):
            arcpy.Delete_management(temp_fc_points)

        # Make a point feature class out of the table.
        x_coords = "Longitude"
        y_coords = "Latitude"
        spat_reference = r'C:\Users\apddsouth\Documents\FMD_Truck_Econ_Paper\ArcMap_stuff\GCS_WGS_1984.prj'
        arcpy.MakeXYEventLayer_management(os.path.join(temp_location, temp_name), x_coords, y_coords,
                                          temp_fc, spatial_reference=spat_reference)
        arcpy.CopyFeatures_management(temp_fc, temp_fc_points)

        # Buffer the feature class.
        print("Buffering for iteration " + str(current_iteration))
        arcpy.Buffer_analysis(in_features=temp_fc_points,
                              out_feature_class=output_GDB,
                              buffer_distance_or_field="%s Kilometers" % str(buffer_dist),
                              line_side="FULL", line_end_type="ROUND",
                              dissolve_option="NONE", dissolve_field="", method="PLANAR")

        #arcpy.Buffer_analysis(in_features="temp_fc_i0_points",
        #                      out_feature_class="C:/Users/apddsouth/Documents/ArcGIS/Default.gdb/blurb",
        #                      buffer_distance_or_field="7 Kilometers", line_side="FULL", line_end_type="ROUND",
        #                      dissolve_option="ALL", dissolve_field="", method="PLANAR")

        # Delete the table and the feature class.
        arcpy.Delete_management(temp_fc, temp_fc_points)


    def select_random_distance_weighted():
        return selected_points

    def infection_spreads():
        # Set up for random seeding in case we want to make the results repeatable.
        if random_seed is not None:
            np.random.seed(seed=random_seed)

        # Randomly sample (without replacement) a number of uninfected farms equal to the current
        # number of farms that should be infected at this stage of the epidemic curve.
        if selection_type == 'random':

            # This variable saves the unique IDs of the farms
            newly_infected_farms = np.random.choice(uninfected_farms,
                                                        int(epidemic_curve[current_iteration]),
                                                        replace=False, p=None)

            # If this is the first iteration, first quarantine zone, then replace the first farm with
            # a dairy farm.
            if previously_infected_farms.size == 0:
                newly_infected_farms[0] == np.random.choice(dairies, 1)# Select one farm from only dairies and replace the first farm of `newly_infected_farms`.

        elif selection_type == 'dw' or selection_type == 'distance_weighted':
            newly_infected_farms = select_random_distance_weighted()

        # Make an array of all the infected farms
        if previously_infected_farms.size == 0:
            # `currently_infected_farms` should be a numpy array that contains the only Unit IDs
            # of the infected farms. It does not hold any demographic information.
            currently_infected_farms = newly_infected_farms
        else:
            # Add the newly infected farms to the array of farms that were infected in a previous iteration.
            currently_infected_farms = np.concatenate((previously_infected_farms, newly_infected_farms), axis=0)

        buffer_infected_farms(currently_infected_farms)

        return currently_infected_farms

    return infection_spreads()



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
