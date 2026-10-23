#!/usr/bin/env python3
"""Character budgets only: not billed token counts or upper bounds."""
from skillmeta import catalog

def main():
    chars = 0
    for path, fm, body in catalog():
        n = len(fm['name'])+len(fm['description'])
        chars += n
        print(f"{fm['name']:<16} description/name {n} chars; body {len(body)} chars")
    print(f'Total name/description: {chars} characters; rough chars/3 = {round(chars/3)}.')
    print('Chinese/model tokenization and host wrappers differ. This is neither real billing nor a maximum.')

if __name__ == '__main__': main()
