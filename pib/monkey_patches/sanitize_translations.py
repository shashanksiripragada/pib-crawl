import os
import sys
from tqdm import tqdm
from argparse import ArgumentParser
from collections import defaultdict
from ilmulti.translator import from_pretrained

from sqlalchemy import or_, and_

# Internal imports.
from .. import db
from ..models import Entry, Link, Translation
from .utils import BatchBuilder

junk = '▁An d ▁it ▁sha ll ▁come ▁to ▁pass ▁ , ▁when ▁it ▁sha ll ▁come ▁to ▁pass ▁ , ▁that ▁it ▁sha ll ▁come ▁to ▁pass ▁ , ▁that ▁it ▁sha ll ▁come ▁to ▁pass ▁ , ▁that ▁it ▁sha ll ▁come ▁to ▁pass ▁ , ▁that ▁it ▁sha ll ▁be ▁ , ▁that ▁it ▁sha ll ▁come ▁to ▁pass ▁ , ▁that ▁it ▁sha ll ▁come ▁to ▁pass ▁ , ▁that ▁it ▁sha ll ▁come ▁to ▁pass ▁ , ▁that ▁it ▁sha ll ▁come ▁to ▁pass ▁ , ▁that ▁it ▁sha ll ▁come ▁to ▁pass ▁ , ▁that ▁it ▁sha ll ▁come ▁to ▁pass ▁ , ▁that ▁it ▁sha ll ▁be ▁ , ▁that ▁it ▁sha ll ▁come ▁to ▁pass ▁ , ▁that ▁it ▁sha ll ▁come ▁to ▁pass ▁ , ▁that ▁it ▁sha ll ▁come ▁to ▁pass ▁ , ▁that ▁it ▁sha ll ▁come ▁to ▁pass ▁ , ▁that ▁it ▁sha ll ▁come ▁to ▁pass ▁ , ▁that ▁it ▁sha ll ▁be ▁ , ▁that ▁it ▁sha ll ▁come ▁to ▁pass ▁ , ▁that ▁it ▁sha ll ▁come ▁to ▁pass ▁ , ▁that ▁it ▁sha ll ▁come ▁to ▁pass ▁ , ▁that ▁it ▁sha ll ▁be ▁ ,'

def clean(model):

    translations = Translation.query.filter(Translation.model == model).all()
    def modify_translation(entry):
        db.session.add(entry)
        db.session.commit()

    for translation in tqdm(translations):
        if junk in translation.translated:
            cleaned = translation.translated.replace(junk, '')
            translation.translated = cleaned         
            modify_translation(translation)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--model', help='model used to translate', required=True)

    args = parser.parse_args()

    clean(args.model)
