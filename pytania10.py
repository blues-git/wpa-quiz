#!/usr/bin/env python3
import sys
import os
import re
import random

# =====================================================================
# UTIL: clear screen
# =====================================================================
def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")

# ANSI BOLD
BOLD = "\033[1m"
RESET = "\033[0m"

# =====================================================================
# HELP
# =====================================================================
def print_help():
    print("""
Użycie:
  quiz.py PLIK_PYTAN.txt [-c N] [-r RANGES] [-a user.csv]
  quiz.py -a user.csv -v master.csv

Opcje:
  --count=N     | -c N        liczba pytań (domyślnie 20)
  --range=X-Y   | -r X-Y      zakresy, np. 1-50,120-150
  --answers=CSV | -a CSV      plik odpowiedzi
  --verify=CSV  | -v CSV      porównanie user.csv vs master.csv

Quiz:
  - pytanie na czystym ekranie
  - q / quit przerywa natychmiast
  - po quizie: lista odpowiedzi + zapis t/n/q

TXT musi mieć strukturę:
  1. Treść pytania (może zawierać nawiasy z art. ustawy)
     a. odpowiedź
     b. odpowiedź
     c. odpowiedź
""")


# =====================================================================
# Wyodrębnienie treści pytania (bez odniesień w nawiasach)
# =====================================================================
def split_question_text(qtext):
    """
    Zwraca (treść właściwa, część nawiasowa)
    np. "Coś tam (art. 10 uobia)" → ("Coś tam", "(art. 10 uobia)")
    """
    m = re.match(r"^(.*?)(\s*\(.*)$", qtext)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    else:
        return qtext, ""


# =====================================================================
# CSV: load + validate
# =====================================================================
def load_answer_key_csv(path):
    if not os.path.exists(path):
        print(f"BŁĄD: plik CSV '{path}' nie istnieje.")
        sys.exit(1)

    answers = {}
    seen = set()
    first = True

    with open(path, "r", encoding="utf-8") as f:
        for lineno, line in enumerate(f,1):
            line=line.strip()
            if not line:
                continue

            cols=[c.strip() for c in line.split(",")]

            # nagłówek?
            if first:
                if not cols[0].isdigit():
                    first=False
                    continue
                first=False

            if not cols[0].isdigit():
                print(f"BŁĄD CSV ({path}:{lineno}): numer pytania nie jest liczbą.")
                sys.exit(1)
            qnum=int(cols[0])

            if qnum in seen:
                print(f"BŁĄD CSV ({path}:{lineno}): duplikat pytania {qnum}.")
                sys.exit(1)
            seen.add(qnum)

            raw=[c.lower() for c in cols[1:] if c.strip()!=""]
            if not raw:
                print(f"BŁĄD CSV ({path}:{lineno}): pytanie {qnum} bez odpowiedzi.")
                sys.exit(1)

            invalid=[c for c in raw if c not in ("a","b","c")]
            if invalid:
                print(f"BŁĄD CSV ({path}:{lineno}): niedozwolone odpowiedzi {invalid}.")
                sys.exit(1)

            if len(set(raw))!=len(raw):
                print(f"BŁĄD CSV ({path}:{lineno}): duplikat odpowiedzi.")
                sys.exit(1)

            answers[qnum]=set(raw)

    return answers


# =====================================================================
# compare user.csv vs master.csv
# =====================================================================
def compare_keys(user_key, master_key):
    print("\n=== WERYFIKACJA user.csv vs master.csv ===\n")

    for qnum, uans in sorted(user_key.items()):
        if qnum not in master_key:
            print(f"BŁĄD: pytanie {qnum} jest w user.csv, ale nie ma go w master.csv.")
            sys.exit(1)

        mans=master_key[qnum]
        if not uans.issubset(mans):
            print(f"BŁĄD: odpowiedzi użytkownika nie są podzbiorem (pytanie {qnum}).")
            print(f"  user:   {sorted(uans)}")
            print(f"  master: {sorted(mans)}")
            sys.exit(1)

    print("WERYFIKACJA POPRAWNA.\n")


# =====================================================================
# parse TXT
# =====================================================================
def load_questions_from_txt(path):
    if not os.path.exists(path):
        print(f"BŁĄD: plik '{path}' nie istnieje.")
        sys.exit(1)

    with open(path,"r",encoding="utf-8") as f:
        lines=[l.rstrip("\n") for l in f]

    q_re=re.compile(r"^\s*(\d+)\.\s*(.*)")
    a_re=re.compile(r"^\s*([abc])\.\s*(.*)")

    questions={}
    current_q=None
    current_text=""
    current_ans=[]

    for line in lines:
        mq=q_re.match(line)
        if mq:
            if current_q is not None:
                questions[current_q]=(current_text, current_ans)

            current_q=int(mq.group(1))
            current_text=mq.group(2).strip()
            current_ans=[]
            continue

        ma=a_re.match(line)
        if ma and current_q is not None:
            current_ans.append((ma.group(1).lower(), ma.group(2).strip()))

    if current_q is not None:
        questions[current_q]=(current_text, current_ans)

    return questions


# =====================================================================
# parse ranges
# =====================================================================
def parse_ranges(rstr, max_q):
    result=set()

    # obsługa --range=1-50
    if "=" in rstr:
        rstr=rstr.split("=",1)[1]

    for seg in rstr.split(","):
        if "-" not in seg:
            print(f"BŁĄD: zakres '{seg}' niepoprawny.")
            sys.exit(1)

        a,b = seg.split("-")
        try:
            start=int(a); end=int(b)
        except:
            print(f"BŁĄD: zakres '{seg}' ma niepoprawne liczby.")
            sys.exit(1)

        if start<1 or end<start:
            print(f"BŁĄD: zakres '{seg}' niepoprawny.")
            sys.exit(1)

        for n in range(start,end+1):
            if n<=max_q:
                result.add(n)

    if not result:
        print("BŁĄD: zakres nie obejmuje żadnych pytań.")
        sys.exit(1)

    return result


# =====================================================================
# MAIN
# =====================================================================
def main():

    # TRYB WERYFIKACJI CSV
    if (("--verify" in sys.argv) or ("-v" in sys.argv)) \
       and (("--answers" in sys.argv) or ("-a" in sys.argv)) \
       and not any(a.endswith(".txt") for a in sys.argv):

        if "--answers" in sys.argv:
            user_csv=sys.argv[sys.argv.index("--answers")+1]
        else:
            user_csv=sys.argv[sys.argv.index("-a")+1]

        if "--verify" in sys.argv:
            master_csv=sys.argv[sys.argv.index("--verify")+1]
        else:
            master_csv=sys.argv[sys.argv.index("-v")+1]

        user_key   = load_answer_key_csv(user_csv)
        master_key = load_answer_key_csv(master_csv)
        compare_keys(user_key, master_key)
        sys.exit(0)

    # QUIZ wymaga pliku TXT
    if len(sys.argv)<2 or sys.argv[1].startswith("-"):
        print_help()
        sys.exit(0)

    txt_file=sys.argv[1]
    questions=load_questions_from_txt(txt_file)
    total_q=len(questions)

    # automatyczne pytania.csv
    base=os.path.splitext(txt_file)[0]
    auto_csv=base+".csv"

    user_key={}
    count=20
    ranges=None

    args=sys.argv[2:]
    for i,arg in enumerate(args):

        if arg.startswith("--count"):
            val = arg.split("=",1)[1] if "=" in arg else args[i+1]
            count=int(val)

        elif arg=="-c":
            count=int(args[i+1])

        elif arg.startswith("--range"):
            val = arg.split("=",1)[1] if "=" in arg else args[i+1]
            ranges=val

        elif arg=="-r":
            ranges=args[i+1]

        elif arg.startswith("--answers"):
            val = arg.split("=",1)[1] if "=" in arg else args[i+1]
            user_key=load_answer_key_csv(val)

        elif arg=="-a":
            user_key=load_answer_key_csv(args[i+1])

    # auto-detect answers
    if not user_key and os.path.exists(auto_csv):
        user_key=load_answer_key_csv(auto_csv)

    # parse ranges
    if ranges:
        allowed=parse_ranges(ranges,total_q)
    else:
        allowed=set(questions.keys())

    pool=[q for q in allowed if q in questions]

    if len(pool)<count:
        print(f"BŁĄD: zakres zawiera tylko {len(pool)} pytań, a żądasz {count}.")
        sys.exit(1)

    selected=random.sample(pool,count)
    user_answers={}

    # QUIZ LOOP
    for qnum in selected:
        clear_screen()
        qtext, answers = questions[qnum]

        core, law = split_question_text(qtext)
        print(f"{qnum}.  {BOLD}{core}{RESET} {law}\n")

        for letter, text in answers:
            print(f"  {BOLD}{letter}){RESET} {text}")

        ans=input("\nOdpowiedź (a/b/c lub q aby przerwać): ").strip().lower()

        if ans in ("q","quit"):
            print("\nQuiz przerwany.\n")
            break

        user_answers[qnum]=ans

    # PRINT RESULTS
    clear_screen()
    print("=== TWOJE ODPOWIEDZI (CSV) ===\n")
    for q,a in sorted(user_answers.items()):
        print(f"{q},{a}")

    # SAVE t/n/q
    while True:
        save=input("\nZapisać do pliku? (t/n/q): ").strip().lower()
        if save in ("t","n","q"):
            break
        print("Wpisz t / n / q.")

    if save=="q":
        print("\nPrzerwano.\n")
        sys.exit(0)

    if save=="t":
        fname=input("Nazwa pliku: ").strip()
        if fname:
            with open(fname,"w",encoding="utf-8") as f:
                for q,a in sorted(user_answers.items()):
                    f.write(f"{q},{a}\n")
            print(f"Zapisano do: {fname}\n")
        else:
            print("Brak nazwy — anulowano.\n")

    # SCORING
    if not user_key:
        return

    print("\n=== OCENA ===\n")
    score=0

    for qnum,ans in sorted(user_answers.items()):
        if qnum not in user_key:
            print(f"[{qnum}] brak w kluczu.")
            continue

        correct=user_key[qnum]
        if ans in correct:
            print(f"[{qnum}] ✔ ({ans}) poprawnie")
            score+=1
        else:
            print(f"[{qnum}] ✘ ({ans}) → poprawne: {sorted(correct)}")

    print(f"\nWYNIK: {score}/{len(user_answers)} poprawnych.\n")


if __name__=="__main__":
    main()

