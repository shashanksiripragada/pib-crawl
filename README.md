# PIB Crawler

## Overview
This repository houses a flask application incrementally built to
extract aligned sentences across multiple languages with a translation
system in place.

The application was originally built to crawl and store
multilingual news articles available at Press Information Bureau
[website](http://pib.gov.in). It can however be repurposed to
prototype, inspect and build for other multilingual sources as well.

We require the web application for the reasons below:

1. Multilingual samples require verification on the alignment and the
   retrieved samples which can easily be done once a web interface is
   created.
2. Storage obviously has to be done in a DBMS due to the nature of the
   data and incremental updates performed efficiently.
3. All tokenization and under the hood processing needs to be repeated
   but hidden from a layman user or expert to gather simple feedback.

## Installation
```bash
# --user is optional
python3 -m pip install -r requirements.txt --user

```
After installing the required packages, run the following script to download the PIB database containing the crawled articles. This script also downloads pretrained multilingual model used for alignment.

```bash
bash scripts/get-resources.sh
```

## Usage
Once we have the DB and pretrained model in place, to extract parallel corpus from the database run the following command.

```bash
bash scripts/export-parallel-corpus.sh

```

## Resources
1. The CVIT-PIB and CVIT-MKB (Mann-Ki-Baat) datasets are available [here](http://preon.iiit.ac.in/~jerin/bhasha/).
2. [Database](http://preon.iiit.ac.in/~jerin/resources/datasets/pib-crawled.db.tar.gz) containing the crawled news articles, which are used to extract parallel corpus.
3. The [Multilingual NMT model](https://iiitaphyd-my.sharepoint.com/:f:/g/personal/shashank_siripragada_alumni_iiit_ac_in/Er-14LL4gatMuE8naqGUQuMBw1QyWeLCocHijQK-eDbsCw?e=f4T3Ol) used for sentence alignment and the associated vocabulary files.
4. We additionally release [multilingual model](https://iiitaphyd-my.sharepoint.com/:f:/g/personal/shashank_siripragada_alumni_iiit_ac_in/Er-14LL4gatMuE8naqGUQuMBw1QyWeLCocHijQK-eDbsCw?e=f4T3Ol) augmented with the PIB corpus.


## Publications

If you use CVIT-PIB and MKB, please cite our [paper](https://www.aclweb.org/anthology/2020.lrec-1.462):
```
@inproceedings{siripragada-etal-2020-multilingual,
    title = "A Multilingual Parallel Corpora Collection Effort for {I}ndian Languages",
    author = "Siripragada, Shashank and Philip, Jerin and Namboodiri, Vinay P. and Jawahar, C V",
    booktitle = "Proceedings of The 12th Language Resources and Evaluation Conference",
    month = may,
    year = "2020",
    address = "Marseille, France",
    publisher = "European Language Resources Association",
    url = "https://www.aclweb.org/anthology/2020.lrec-1.462",
    pages = "3743--3751",
    language = "English",
    ISBN = "979-10-95546-34-4",
}
```