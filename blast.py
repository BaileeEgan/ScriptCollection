#!/usr/bin/python3

#
# Description:
#  - Wrapper script for running BLAST through Python
#  - Automatically detects which BLAST program to use (BLASTN, BLASTP, TBLASTN, BLASTX)
#  - Specify query, db, and output directory with other BLAST options supported
#  - Outputs params file and TSV of BLAST hits
#
# Requirements
#  - The BLAST suite must be in your $PATH variable (in this script, BLAST is loaded as a module)
#

import os
import sys
import argparse
from Bio.Blast.Applications import *
from Bio import SeqIO
from datetime import datetime

def main(arguments):

	parser = argparse.ArgumentParser(description = __doc__, formatter_class = argparse.RawDescriptionHelpFormatter)

	# Required parameters

	parser.add_argument("-q", "--query", help="Query file", required=True)
	parser.add_argument("-d", "--db", help="Query file", required=True)
	parser.add_argument("-o", "--out", help="Output directory", required=True)

	# Optional parameters

	parser.add_argument("-e", "--evalue", help="E-value threshold (default: 10)", default="10.0")
	parser.add_argument("-t", "--threads", help="Threads (default: 1)", type=int, default=1)
	parser.add_argument("--max_hsps", help="Max HSPs (default: 1)", type=int, default=1)
	parser.add_argument("--max_targets", help="Max targets (default: 15)", type=int, default=15)
	parser.add_argument("--min_hsp_cov", help="Min HSP coverage [0-100] (default: 0.0)", type=float, default=0.0)
	parser.add_argument("--query_is_prot", help="Query is protein", action="store_true")
	parser.add_argument("--query_is_nucl", help="Query is nucleotide", action="store_true")


	args = parser.parse_args(arguments)	# Get args as args.name


	### Generate output file names and sets file paths as absolute ###


	query_basename = os.path.basename(args.query)
	db_basename = os.path.basename(args.db)
	out_prefix = "%s__%s__%s" % (query_basename, db_basename, args.evalue)
	out_tsv = args.out + "/" + out_prefix + ".tsv"
	out_params = args.out + "/" + out_prefix + ".params"

	if not os.path.isabs(args.query):
		args.query = os.path.abspath(os.getcwd()) + "/" + args.query
	if not os.path.isabs(args.db):
		args.db = os.path.abspath(os.getcwd()) + "/" + args.db


	### Determine the query type ###


	query_type = ""
	if args.query_is_nucl:
		query_type = "N"
	elif args.query_is_prot:
		query_type = "P"
	else:				# We infer from the first 5000 characters of the sequence 
		query_seqs = ""
		for record in SeqIO.parse(args.query, "fasta"):
			query_seqs += str(record.seq).upper()
			if len(query_seqs) > 5000:
				break

		amino_acids = ["R", "D", "Q", "E", "H", "I", "L", "K", "M", "F", "P", "S", "W", "Y", "V"]	
		if any([(aa in query_seqs) for aa in amino_acids]):
			query_type = "P"
		else:
			query_type = "N"


	### Determine database type ###


	db_type = ""
	if os.path.isfile(args.db + ".nin"):
		db_type = "N"
	elif os.path.isfile(args.db + ".pin"):
		db_type = "P"
	else:
		print("Error: Cannot find BLAST db for %s" % args.db)
		exit()


	### Determine which BLASTP program to use ###


	os.system("module load blast")
	blast = None

	if query_type == "N" and db_type == "N":
		blast = NcbiblastnCommandline
	elif query_type == "P" and db_type == "P":
		blast = NcbiblastpCommandline
	elif query_type == "N" and db_type == "P":
		blast = NcbiblastxCommandline
	elif query_type == "P" and db_type == "N":
		blast = NcbitblastnCommandline


	### Run BLAST ###


	outfmt = ["qseqid", "sacc", "stitle", "qstart", "qend", "sstart", "send", "qlen", "slen", "length", "mismatch", "pident", "qcovs", "qcovhsp", "score", "bitscore", "evalue"]

	if blast is not None:

		if not os.path.isdir(args.out):
			os.mkdir(args.out)
	

		### Create params log ###


		vars_args = vars(args)
		log = ["Date\t%s" % datetime.now()]
		log += [ "%s\t%s" % (name, vars_args[name]) for name in vars_args]
		log += ["\nColumn information"]
		log += ["%s\t%s" % (i, outfmt[i]) for i in range(len(outfmt))]

		print("\n****************\n")
		print("Running BLAST\n")
		print("\n".join(log) + "\n")
		print("\n****************\n")
		

		with open(out_params, "w") as f:
			f.writelines("\n".join(log) + "\n")


		### Run BLAST ###


		blast = NcbiblastpCommandline	
		cmd = blast(query = args.query, db = args.db, evalue = args.evalue, outfmt = "6 " + " ".join(outfmt), out = out_tsv, max_target_seqs = args.max_targets, max_hsps = args.max_hsps, qcov_hsp_perc = args.min_hsp_cov, num_threads=args.threads) 
		stdout,stderr = cmd()


	else:
		print("Unable to determine correct BLAST version")

if __name__ == "__main__":
	sys.exit(main(sys.argv[1:]))