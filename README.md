Repository for long-trip accessibility examples. This repository includes a self contained
example on a randomly generated Supply Network Graph (SNG) in random.ipynb. Also included
is an example for the California SNG. Running the California example requires pulling data and creating the SNG which will take some time. Note that AFDC is updated nightly so the
stations pulled from AFDC will not exactly match those pulled when the associated paper was
written.

You may reach out to the repository owner for instructions on making the atlas.json file.

Order of operations for the California example:

1. Run either make_data_structure.sh or make_data_structure.py
	requires modifying keys.txt

You will need to register a key with AFDC. When this is done make a file called keys.txt.

This file should contain:

afdc_key="Your Key Here"

2. Make_Empty_Graph.ipynb

3. Add_Adjacency.ipynb

4. California.ipynb