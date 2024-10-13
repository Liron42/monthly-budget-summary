# -*- coding: utf-8 -*-
import codecs
from datetime import datetime
import sys
import json
import os

RETRY_ATTEMPTS_CLASSIFY = 5
CASH_CATEGORIES = []


def init_summary_internal(categories):
    summary_internal = {}
    for category in categories:
        summary_internal[category] = {}
        summary_internal[category]["total"] = 0
    return summary_internal


def init_rules(keys):
    rules = ""
    for key, value in keys.items():
        rules += "%s for %s\n" % (key, value)
    return rules


def init_summary(categories_keys, month_format):
    summary_internal = init_summary_internal(categories_keys)
    try:
        with open('summary_per_month/summary_%s.json' % month_format) as file:
            summary_origin = json.load(file, encoding='utf-8')
            return summary_internal, summary_origin, True
    except:
        return summary_internal, None, False


def init_business_places():
    with open("business_places.json") as file:
        return json.load(file)

def calculate(summary, category, amount, element, rules, keys):
    if summary.setdefault(category, None) is None:
        summary[category] = {"total": 0}
    if element not in summary[category].keys():
        summary[category][element] = amount * -1
    else:
        summary[category][element] += (amount * -1)
    summary[category]["total"] += (amount * -1)


def get_classification(element, rules, keys, amount):
    valid_input = False
    retry_attempts_classify = RETRY_ATTEMPTS_CLASSIFY
    while not valid_input and retry_attempts_classify > 0:
        data_input = input(
            "please classify %s, amount: %s with the following rules:\n%s\nyour input:\n"
            "In case you would like to add new category please set 0\n" % (
                element, amount * -1, rules))
        if data_input == "0":
            new_category = input("category name:\n")
            keys[len(keys.keys()) + 1] = new_category
            rules += "%s for %s\n" % (len(keys.keys()), new_category)
            return new_category, rules
        try:
            result = keys[int(data_input)]
            valid_input = True
            return result, rules
        except:
            retry_attempts_classify -= 1
            print("You have inserted an invalid classification, " \
                  "please try again. Note that you have left with %d chances" % retry_attempts_classify)

    print("Failed to classify, try again when you know your expanses")
    sys.exit(1)


def create_categories():
    categories = {}
    with open("plan.json") as file:
        plan = json.load(file)
    i = 1
    for k in plan.keys():
        categories[i] = k
        i += 1
    return categories


def add_missing_places_and_sum(summary):
    total_expanses = 0
    for k, v in summary.items():
        total_expanses += summary[k]["total"]
    return summary, total_expanses


def init_transactions_maps(month):
    transactions_maps = []
    # os.system("/opt/homebrew/bin/node scraper.js %s" % month)  # fix this
    file_names = ['output_amx', 'output_dror', 'output_new', "output_dror_cal"]
    for file_name in file_names:
        with codecs.open('credit_card_output/%s.json' % file_name) as f:
            transactions_maps.append(json.load(f))
    return transactions_maps


def recalculate(month_format):
    with open('summary_per_month/summary_%s.json' % month_format, 'r', encoding='utf-8') as file:
        summary_origin = json.load(file)
        for category in summary_origin.keys():
            new_total = 0
            for item, value in summary_origin[category].items():
                if item == 'total':
                    continue
                else:
                    new_total += value
            summary_origin[category]['total'] = new_total
    with codecs.open('summary_per_month/summary_%s.json' % month_format,'w', encoding='utf-8') as output:
        json.dump(summary_origin, output, indent=4, ensure_ascii=False)


def main():
    month = sys.argv[1]
    mode = sys.argv[2]
    month_format = str(month) + "_" + str(datetime.now().year)
    if str(mode) == 'recalculate':
        recalculate(month_format)
        sys.exit(0)
    transactions_map = init_transactions_maps(month)
    categories_keys = create_categories()
    rules = init_rules(categories_keys)
    business_places = init_business_places()
    summary, summary_origin, update_mode = init_summary(categories_keys.values(), month_format)

    for transaction_map in transactions_map:
        for account in transaction_map["accounts"]:
            for transaction in account["txns"]:
                if transaction["date"].find("%s-%s" % (datetime.now().year, month)) != -1:
                    element = transaction["description"]
                    amount = transaction["chargedAmount"]
                    if business_places.setdefault(element, None) and (element.find("העברה ב BIT")) == -1 and (element.find("העברה בBIT")) == -1 and (element.find("PAYBOX")) == -1 and (element.find("WOLT")) == -1 and (element.find("BIT")) == -1:
                        calculate(summary, business_places[element], amount, element, rules, categories_keys)
                    else:
                        rules_to_update = rules
                        classification, rules = get_classification(element, rules_to_update, categories_keys, amount)
                        business_places[element] = classification
                        calculate(summary, classification, amount, element, rules, categories_keys)

    with codecs.open('business_places.json', 'w', encoding='utf-8') as output:
        json.dump(business_places, output, indent=4, ensure_ascii=False)

    summary, total_expenses = add_missing_places_and_sum(summary)
    print("total expanses for this month: %s" % total_expenses)
    with codecs.open('summary_per_month/summary_%s.json' % month_format, 'w', encoding='utf-8') as output:
        json.dump(summary, output, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    main()
