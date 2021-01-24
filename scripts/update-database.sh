#!/bin/bash


mkdir -p crawl-cache/
python3 -m pib.tools.scrape --path crawl-cache/Dec2020 --begin 1646520 --end 1684643
