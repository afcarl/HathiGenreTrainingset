HathiTrust training
===================

This repo currently includes Python scripts that I am using to munge page-level training data for a project, "ÄúUnderstanding Genre in a Collection of a Million Volumes."Äù

The actual classification scripts (in Java) are in [a different repo, intuitively named pages.](https://github.com/tedunderwood/pages)

The subdirectory /olddata also includes older training data I used for an earlier volume-level classification project.

Scripts
---------

Evaluate.py - Primary script I'm using to assess accuracy of a single model.

Coalescer.py - Module that smooths predictions as part of Evaluate.

Ensemble.py - Combines multiple models into an ensemble and assesses collective accuracy.

SonicScrewdriver.py - A collection of utilities.





