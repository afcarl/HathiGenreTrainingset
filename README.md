HathiTrust training data
==================

This repo currently includes Python scripts that I am using to munge page-level training data for a project, "Understanding Genre in a Collection of a Million Volumes."

The actual classification scripts (in Java) are in [a different repo, intuitively named pages.](https://github.com/tedunderwood/pages)

The subdirectory /olddata also includes older training data I used for an earlier volume-level classification project.

Scripts
---------
I can't write an account of every single Python script in the repo; a lot of them are one-offs. Here are the most significant.

Evaluate.py - Primary script I'm using to assess accuracy of a single model.

Coalescer.py - Module that smooths predictions as part of Evaluate.

Ensemble.py - Combines multiple models into an ensemble and assesses collective accuracy.

MetadataFeatures.py - Script that adds global "metadata features" to the pagefeatures files.

SelectFeatures.py - Script that I used to generate vocabularies.

SonicScrewdriver.py - A collection of utilities.

Triads
--------

The scripts in this subdirectory represent a mostly-failed experiment to improve my approach to smoothing by training models using a lot of additional data. If you wanted to glorify it, you could call it a quasi- semi- Conditional Random Field approach. However, in practice, it didn't produce better results than the naive ad hoc rules embodied in Coalescer, so this is now a dead end.





