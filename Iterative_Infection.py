# This script was designed to create a series of quarantine zones based on random points,
# simulating an infection curve.

import random
import sys

epidemic_curve = []

def create_quarantine_zone(input_point_data, output_path, current_iteration, selection_type='random'):
    """
    Set selection_type='random' for equal probability of any point being selected, and selection_type='dw'
    or selection_type='distance_weighted' for selecting points randomly weighted by distance.
    :param input_point_data: The file path to the point shapefile or feature class with the farms to be infected.
    :param current_iteration: The current step of the progression through the epidemic curve.
    :return:
    """

    def buffer(input_points, output_file_path, buffer_dist=7):
        arcpy.Buffer_analysis(in_features=input_points,
                              out_feature_class=output_file_path,
                              buffer_distance_or_field="%s Kilometers" %str(buffer_dist),
                              line_side="FULL", line_end_type="ROUND",
                              dissolve_option="ALL", dissolve_field="", method="PLANAR")

    def select_random():
        return selected_points

    def select_random_distance_weighted():
        return selected_points

    def infection_spreads():
        if selection_type=='random':
            buffer(select_random(), output_path)
        elif selection_type=='dw' or selection_type=='distance_weighted':
            buffer(select_random_distance_weighted(), output_path)


    def infection_wanes():
        # Select which farms are no longer infected entirely randomly, not distance weighted.
        buffer(select_random(), output_path)

    previous_infection_count = epidemic_curve[current_iteration-1]
    current_infection_count = epidemic_curve[current_iteration]
    if current_infection_count - previous_infection_count > 0:
        infection_spreads(...)
    elif current_infection_count - previous_infection_count < 0:
        infection_wanes(...)

if __name__ == '__main__':
    num_iterations = len(epidemic_curve)
    for current_iteration in range (1, num_iterations+1):
        create_quarantine_zone(all_FLAPS, current_iteration)