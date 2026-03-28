#!/usr/bin/env python3
import sys
import os
import re
import random
import time

# =====================================================================
# UTILITIES
# =====================================================================

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")

BOLD  = "\033[1m"
RED   = "\033[31m"
GREEN = "\033[32m"
RESET = "\033[0m"


# =====================================================================
# HELP
# =====================================================================

def print_help():
    print("""
Użycie:
  quiz.py PLIK_PYTAN.txt [-c N] [-r RANGES] [-a user.csv] [-b] [-S]
  quiz.py -a user.csv -v master.csv

Opcje:
  --count=N     | -c N         liczba pytań (domyślnie 20)
  --range=X-Y   | -r X-Y       zakresy pytań, np. 1-50,120-150
  --answers=CSV | -a CSV       klucz odpowiedzi
  --verify=CSV  | -v CSV       porównanie user.csv z master.csv
  --browse      | -b           tryb przeglądania (od razu pokazuje wynik pytania)
  --no-stats    | -S           wyłącza system statystyk
""")


# =====================================================================
# Wyodrębnienie treści pytania (część w nawiasach nie jest pogrubiona)
# =====================================================================

def split_question_text(qtext):
    m = re.match(r"^(.*?)(\s*\(.*)$", qtext)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return qtext, ""


# =====================================================================
# CSV: wczytanie i walidacja
# =====================================================================

def load_answer_key_csv(path):
    if not os.path.exists(path):
        print(f"BŁĄD: plik CSV '{path}' nie istnieje.")
        sys.exit(1)

    answers = {}
    seen = set()
    first = True

    with open(path,"r",encoding="utf-8") as f:
        for lineno,line in enumerate(f,1):
            line=line.strip()
            if not line:
                continue

            cols=[c.strip() for c in line.split(",")]

            if first:
                if not cols[0].isdigit():
                    first=False
                    continue
                first=False

            if not cols[0].isdigit():
                print(f"BŁĄD CSV {path}:{lineno} – numer pytania nie jest liczbą.")
                sys.exit(1)

            qnum=int(cols[0])
            if qnum in seen:
                print(f"BŁĄD CSV {path}:{lineno} – duplikat pytania {qnum}.")
                sys.exit(1)
            seen.add(qnum)

            raw=[c.lower() for c in cols[1:] if c.strip()!=""]
            if not raw:
                print(f"BŁĄD CSV {path}:{lineno} – brak odpowiedzi.")
                sys.exit(1)

            invalid=[c for c in raw if c not in ("a","b","c")]
            if invalid:
                print(f"BŁĄD CSV {path}:{lineno} – niedozwolone odpowiedzi {invalid}.")
                sys.exit(1)

            if len(set(raw))!=len(raw):
                print(f"BŁĄD CSV {path}:{lineno} – duplikat odpowiedzi.")
                sys.exit(1)

            answers[qnum]=set(raw)

    return answers


# =====================================================================
# Porównanie CSV (user vs master)
# =====================================================================

def compare_keys(user_key, master_key):
    print("\n=== WERYFIKACJA user.csv vs master.csv ===\n")
    for qnum,uans in sorted(user_key.items()):
        if qnum not in master_key:
            print(f"BŁĄD: pytanie {qnum} istnieje w user.csv, brak w master.csv.")
            sys.exit(1)
        mans=master_key[qnum]
        if not uans.issubset(mans):
            print(f"BŁĄD: odpowiedzi user nie są podzbiorem (pytanie {qnum}).")
            print(f"   user:   {sorted(uans)}")
            print(f"   master: {sorted(mans)}")
            sys.exit(1)
    print("WERYFIKACJA POPRAWNA.\n")


# =====================================================================
# PARSE TXT PYTAŃ
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
    qnum=None
    text=""
    answers=[]

    for line in lines:
        mq=q_re.match(line)
        if mq:
            if qnum is not None:
                questions[qnum]=(text,answers)
            qnum=int(mq.group(1))
            text=mq.group(2).strip()
            answers=[]
            continue

        ma=a_re.match(line)
        if ma and qnum is not None:
            answers.append((ma.group(1), ma.group(2).strip()))

    if qnum is not None:
        questions[qnum]=(text,answers)

    return questions


# =====================================================================
# PARSE RANGES
# =====================================================================

def parse_ranges(rstr, max_q):
    result=set()

    if "=" in rstr:
        rstr=rstr.split("=",1)[1]

    for seg in rstr.split(","):
        if "-" not in seg:
            print(f"BŁĄD: zakres '{seg}' niepoprawny.")
            sys.exit(1)
        a,b=seg.split("-")
        try:
            start=int(a); end=int(b)
        except:
            print(f"BŁĄD: liczby w zakresie '{seg}' niepoprawne.")
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
# STATYSTYKI: wczytanie / zapis
# =====================================================================

def load_stats(stats_path):
    if not os.path.exists(stats_path):
        return {}

    stats={}
    with open(stats_path,"r",encoding="utf-8") as f:
        for line in f:
            line=line.strip()
            if not line:
                continue
            cols=[c.strip() for c in line.split(",")]
            if len(cols)!=3:
                continue
            try:
                q=int(cols[0])
                good=int(cols[1])
                bad=int(cols[2])
            except:
                continue
            stats[q]=(good,bad)
    return stats


def save_stats(stats_path, stats_dict):
    with open(stats_path,"w",encoding="utf-8") as f:
        for q,(g,b) in sorted(stats_dict.items()):
            f.write(f"{q},{g},{b}\n")


# =====================================================================
# WAGA PYTANIA (wg Twojego algorytmu)
# =====================================================================

def compute_question_weight(good, bad):
    T = good + bad

    if T == 0:
        return 100        # nowe pytanie

    if bad == 0:
        return 1          # opanowane

    ratio = bad / T       # im większy udział błędów, tym większa waga
    w = 1 + ratio * 20

    # stabilizacja (nie faworyzować pojedynczych strzałów)
    w *= 1 + min(T,10)/20

    # zabezpieczenia
    if w < 1:
        w = 1
    if w > 25:
        w = 25

    return w


# =====================================================================
# LOSOWANIE Z UWZGLĘDNIENIEM STATYSTYK
# =====================================================================

def weighted_random_selection(pool, stats, count):
    """
    pool — lista numerów pytań dostępnych po filtrach
    stats — słownik {q: (good,bad)}
    """
    new_ones   = [q for q in pool if q not in stats]
    others     = [q for q in pool if q     in stats]
    random.shuffle(new_ones)  # LOSOWANIE nowego zbioru

    # Jeśli całkowicie nie ma statystyk — wybierz losowo
    if len(others) == 0:
        return random.sample(new_ones, count)

    random.shuffle(others)  # LOSOWANIE nowego zbioru

    selected=[]

    # 1 — najpierw nowe pytania
    for q in new_ones:
        if len(selected) < count:
            selected.append(q)
        else:
            break

    remaining = count - len(selected)
    if remaining <= 0:
        return selected[:count]

    # 2 — pozostałe pytania losowane wg wag
    weighted=[]
    for q in others:
        g,b = stats[q]
        w = compute_question_weight(g,b)
        weighted.append((q,w))

    # jeśli z jakiegoś powodu brak — fallback do czystego losowania
    if not weighted:
        return selected + random.sample(pool, remaining)

    # normalizacja wag
    total_weight = sum(w for _,w in weighted)
    if total_weight == 0:
        return selected + random.sample(others, remaining)

    chosen=set(selected)
    while len(selected) < count:
        r = random.random() * total_weight
        acc=0
        for q,w in weighted:
            acc+=w
            if acc >= r:
                if q not in chosen:
                    chosen.add(q)
                    selected.append(q)
                break

    return selected


# =====================================================================
# MAIN
# =====================================================================

def main():

    # TRYB WERYFIKACJI CSV (nie wymaga TXT)
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

    # QUIZ / BROWSE wymaga TXT
    if len(sys.argv)<2 or sys.argv[1].startswith("-"):
        print_help()
        sys.exit(0)

    txt_file=sys.argv[1]
    questions=load_questions_from_txt(txt_file)
    total_q=len(questions)

    # auto-CSV
    base=os.path.splitext(txt_file)[0]
    auto_csv=base+".csv"

    # statystyki
    stats_path=base+".stats"

    # OPCJE - wartości domyślne
    user_key={}
    count=20
    ranges=None
    browse=True
    no_stats=False
    exam=False

    args=sys.argv[2:]
    for i,arg in enumerate(args):

        # long
        if arg.startswith("--count"):
            val = arg.split("=",1)[1] if "=" in arg else args[i+1]
            count=int(val)

        elif arg.startswith("--range"):
            val = arg.split("=",1)[1] if "=" in arg else args[i+1]
            ranges=val

        elif arg.startswith("--answers"):
            val = arg.split("=",1)[1] if "=" in arg else args[i+1]
            user_key=load_answer_key_csv(val)

        elif arg=="--browse":
            browse=True

        elif arg=="--no-stats":
            no_stats=True

        # short
        elif arg=="-c":
            count=int(args[i+1])

        elif arg=="-r":
            ranges=args[i+1]

        elif arg=="-a":
            user_key=load_answer_key_csv(args[i+1])

        elif arg=="-b":
            browse=True

        elif arg=="-S":
            no_stats=True

        elif arg == "--exam":
            browse = False
            exam = True

        elif arg == "-e":
            browse = False
            exam = True

    # auto-detect CSV
    if not user_key and os.path.exists(auto_csv):
        user_key=load_answer_key_csv(auto_csv)

    # zakres
    if ranges:
        allowed=parse_ranges(ranges,total_q)
    else:
        allowed=set(questions.keys())

    pool=[q for q in allowed if q in questions]

    if len(pool)<count:
        print(f"BŁĄD: dostępnych tylko {len(pool)} pytań, a żądasz {count}.")
        sys.exit(1)

    # statystyki
    stats = {} if no_stats else load_stats(stats_path)

    # LOSOWANIE
    selected = weighted_random_selection(pool, stats, count)

    user_answers={}
    correct_count=0

    # =================================================================
    # TRYB PRZEGLĄDANIA (natychmiastowa odpowiedź)
    # =================================================================
    if browse:
        for qnum in selected:
            clear_screen()

            qtext, answers = questions[qnum]
            core, law = split_question_text(qtext)

            print(f"{qnum}.  {BOLD}{core}{RESET}\n{law}\n")
            for letter,text in answers:
                print(f"  {BOLD}{letter}){RESET} {text}")

            ans=input("\nOdpowiedź (a/b/c lub q): ").strip().lower()
            if ans in ("q","quit"):
                print("\nPrzerwano.\n")
                break

            user_answers[qnum]=ans

            if qnum in user_key and ans in user_key[qnum]:
                print(f"{GREEN}✔ Poprawnie!{RESET}")
                correct_count+=1
            else:
                print(f"{RED}✘ Błąd.{RESET}")
                if qnum in user_key:
                    print(f"Poprawne: {sorted(user_key[qnum])}")

            input("\nENTER aby kontynuować...")

        # aktualizacja statystyk
        if not no_stats:
            for qnum,ans in user_answers.items():
                g,b = stats.get(qnum,(0,0))
                if qnum in user_key and ans in user_key[qnum]:
                    g+=1
                else:
                    b+=1
                stats[qnum]=(g,b)
            save_stats(stats_path,stats)

        total = len(user_answers)
        print(f"\nWYNIK: {correct_count}/{total} poprawnych.\n")
        return


    # =================================================================
    # TRYB EGZAMINOWY
    # =================================================================
    for qnum in selected:
        clear_screen()

        qtext, answers = questions[qnum]
        core, law = split_question_text(qtext)
        print(f"{qnum}.  {BOLD}{core}{RESET}\n{law}\n")

        for letter,text in answers:
            print(f"  {BOLD}{letter}){RESET} {text}")

        ans=input("\nOdpowiedź (a/b/c lub q): ").strip().lower()
        if ans in ("q","quit"):
            print("\nPrzerwano.\n")
            break

        user_answers[qnum]=ans

    # druk wyników
    clear_screen()
    print("=== TWOJE ODPOWIEDZI ===\n")
    for q,a in sorted(user_answers.items()):
        print(f"{q},{a}")

    # zapisywanie t/n/q
    while True:
        s=input("\nZapisać odpowiedzi? (t/n/q): ").strip().lower()
        if s in ("t","n","q"):
            break
        print("Wpisz t / n / q.")

    if s=="q":
        print("\nPrzerwano.\n")
        return
    if s=="t":
        fname=input("Nazwa pliku: ").strip()
        if fname:
            with open(fname,"w",encoding="utf-8") as f:
                for q,a in sorted(user_answers.items()):
                    f.write(f"{q},{a}\n")
            print("Zapisano.")
        else:
            print("Anulowano zapis.")

    # OCENA
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
            print(f"[{qnum}] {GREEN}✔ ({ans}) poprawnie{RESET}")
            score+=1
        else:
            print(f"[{qnum}] {RED}✘ ({ans}) → poprawne: {sorted(correct)}{RESET}")

    print(f"\nWYNIK: {score}/{len(user_answers)} poprawnych.\n")

    # --- aktualizacja statystyk ---
    if not no_stats:
        for qnum, ans in user_answers.items():
            good, bad = stats.get(qnum, (0, 0))

            # qnum to numer pytania z pliku źródłowego (OK!)
            if qnum in user_key and ans in user_key[qnum]:
                good += 1
            else:
                bad += 1

            stats[qnum] = (good, bad)

    save_stats(stats_path, stats)

if __name__=="__main__":
    main()
