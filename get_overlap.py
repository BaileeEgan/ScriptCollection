#!/usr/bin/python3

# Description:
#  Calculates the number of elements shared across overlapping sets of files.
#  Input is a list of files separated by commas.
#  Files contain one element per line, or elements 
#    can be extracted from a specified columns and delimiter


import sys
import argparse
import enum
import itertools

def file_list(file_string):
	return(file_string.split(','))

def main(arguments):

	parser = argparse.ArgumentParser(description = __doc__, formatter_class = argparse.RawDescriptionHelpFormatter)

	parser.add_argument("-f", "--files", help="Input file list", type=file_list, required=True)
	parser.add_argument("-k", "--col", help="Column index (starts at 0)", type=int, nargs="?", default=-1)
	parser.add_argument("-d", "--delim", help="Delimiter (default: tab)", default="\t")
	parser.add_argument("-o", "--out", help="Output file", default=sys.stdout, type=argparse.FileType("w"))

	args = parser.parse_args(arguments)	# Get args as args.name

	### Initialize enums, setting enum for each bit ###

	files_to_enum = {}
	for i in range(len(args.files)):
		files_to_enum[args.files[i]] = 1 << i		
	FileEnum = enum.IntFlag('FileEnum', files_to_enum)

	### Reading and recording values from the file list ###

	value_enums = {}

	def extract_value_from_line (line):
		line = line.strip()
		value = line
		if args.col > -1:
			cols = line.split(args.delim)
			if args.col < len(cols):
				value = cols[args.col]		
		return value

	def add_value_to_dict_from (value, file):
		flag = FileEnum[file]
		if value not in value_enums:
			value_enums[value] = flag
		else:
			value_enums[value] |= flag


	for file in args.files:
		with open(file, "r") as f:
			for line in f.readlines():
				value = extract_value_from_line(line)
				add_value_to_dict_from(value, file)

	print(value_enums)


	### Initializing each set, or combination of each file ###

	set_names = []
	set_enums = []
	set_exclusive = []
	set_inclusive = []

	for i in range(1, len(args.files) + 1):
		for overlap_set in itertools.combinations(args.files, i):
			set_names.append(overlap_set)
			e = 0
			for f in overlap_set:
				e |= FileEnum[f]
			set_enums.append(e)
			set_exclusive.append([])
			set_inclusive.append([])

	### Assign values to each set based on their matching enums ###

	for i in range(len(set_names)):

		set_name = set_names[i]
		set_enum = set_enums[i]

		for value in value_enums:
			value_enum = value_enums[value]
			if value_enum == set_enum:
				set_exclusive[i].append(value)

			if (value_enum & set_enum) == set_enum:
				set_inclusive[i].append(value)


	# Uncomment for to see values contained by each set
	#for i in range(len(set_names)):
	#	print("%s %s" %(set_names[i], set_exclusive[i]))

	### Compile output ###

	out = []

	out.append("Set\tExclusive\tInclusive")

	for i in range(len(set_names)):
		out.append("%s\t%s\t%s" %(",".join(set_names[i]), len(set_exclusive[i]), len(set_inclusive[i])))

	### Print output ###

	out = "\n".join(out) + "\n"

	if args.out == sys.stdout:
		print(out, file = sys.stdout)
	else:
		with(args.out) as f:
			f.writelines(out)

if __name__ == "__main__":
	sys.exit(main(sys.argv[1:]))
