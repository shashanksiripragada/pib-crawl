

This repository houses a flask application incrementally built to
extract aligned sentences across multiple languages with a translation
system in place.


The application was originally built to crawl and store structured the
multilingual news articles available at Press Information Bureau
[website](http://pib.gov.in).  It can however be repurposed to
prototype, inspect and build for other multilingual sources as well.

We require the web application for the reasons below:

1. Multilingual samples require verification on the alignment and the
   retrieved samples which can easily be done once a web interface is
created.
2. Storage obviously has to be done in a DBMS due to the nature of the
   data and incremental updates performed efficiently.
3. All tokenization and under the hood processing needs to be repeated
   but hiddeen from a layman user or expert to gather simple feedback.

Resources:

1. [Database](https://iiitaphyd-my.sharepoint.com/:u:/g/personal/shashank_siripragada_alumni_iiit_ac_in/EamxIkTjZuNGngYR1c82PmoBSi5FII39GGwHwTaVt3E_ig?e=wwtqHv) containing the crawled news articles, which are used to 
    extract parallel corpus.
2. The [NMT model]() use for sentence alignment. 
