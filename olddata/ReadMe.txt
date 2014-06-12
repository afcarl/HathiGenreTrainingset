ReadMe.txt

This folder contains training data used to create genre models. The word counts are drawn from HathiTrust volumes, and volumes are identified by HathiTrust volume ID.

Some idosyncrasies of the tokenizing process: I don't generally "stem" words, but I do truncate apostrophe-s.

Also, instead of recording specific Arabic numerals, I collapse them all into a feature "arabicnumeral". Likewise with Roman numerals. Obvs, I don't count I as a Roman numberal.

These quirks are ways of getting the maximum bang for my buck if I'm only looking at a small number (say 1000 or 2000) of common features. The prevalence of numbers is useful info, but it's not well represented by feature counts of *individual* numbers. So I prefer to have a count for "arabicnumeral" in general.

In a more general data structure that had to serve other researchers, one would naturally store the frequencies of each individual token. Generalization of this sort could be performed while extracting feature counts from an index, instead of generalizing in the tokenizing process and storing generalized data.

Some idiosyncrasies of the metadata: I have a column for genre. Generally the options are

bio - biography
non - other nonfiction
poe - poetry/verse
dra - drama
fic - prose nonfiction

However, it's also possible to have dra|poe or poe|dra. The order doesn't matter. Both of these codes indicate that a volume contains both drama and poetry. (Often, it's a work of dramatic poetry.) In training models I include such volumes in the training sets for both genres.

"Bio" could logically be folded into nonfiction, but I find it useful to break it out, because it's the class of nonfiction most difficult to disambiguate from prose fiction.